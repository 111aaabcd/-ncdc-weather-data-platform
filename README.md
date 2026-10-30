# NCDC 气象数据分析与可视化

用 NOAA/NCEI 的 GSOD 日观测数据做气温和降水分析。数据范围是 2019—2024 年，选取北京、上海、广州、成都、武汉、哈尔滨、乌鲁木齐和昆明的代表站点。处理后保留 17,365 条日记录，按城市和月份汇总为 576 条数据。

![页面预览](docs/dashboard.png)

## 处理过程

1. 读取原始 CSV，解析日期和数值字段，将缺失标记转为空值。
2. 把温度从华氏度换算为摄氏度、降水从英寸换算为毫米，按站点和日期去重，检查取值范围。
3. 按城市、年份和月份计算平均温度、最高最低温、降水量及有效记录数。
4. 将明细、汇总和模型结果写入 SQLite，由 Django 接口提供给前端。
5. 用 React 和 ECharts 展示气温曲线、降水对比和地图，支持城市与年份筛选。

另外比较了季节朴素、谐波趋势、月份哑变量趋势及混合模型。2023 年用于选型，2024 年用于独立测试，评价指标为 MAE 和 RMSE。

## 运行

需要 Python 3.10+、Node.js 20+ 和 npm。仓库自带 48 个公开气象 CSV 样本，首次运行需要联网安装依赖。

Windows 下在项目根目录执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\quick_start.ps1
```

浏览器访问 <http://127.0.0.1:8000/>。后续启动使用 `scripts\start.ps1`，在启动窗口按 `Ctrl+C` 停止。

也可以手动安装和运行。创建并激活 Python 虚拟环境后：

```bash
pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
python -m pipeline.run_pipeline
python backend/manage.py runserver 127.0.0.1:8000 --noreload
```

## 目录

| 目录 | 内容 |
| --- | --- |
| `data/raw/` | GSOD 原始数据样本 |
| `pipeline/` | 清洗、聚合、预测评估和入库 |
| `backend/` | Django 接口 |
| `frontend/` | React 页面 |
| `hadoop/`、`hive/`、`sqoop/`、`mysql/` | 大数据扩展脚本 |
| `scripts/` | Windows 安装和启停脚本 |
| `tests/` | Python 测试 |

## 校验与数据口径

先运行数据处理流程，再执行测试：

```bash
python -m pipeline.run_pipeline
python -m unittest discover -s tests -v
```

7 项测试覆盖数据范围、月度唯一性、模型评估、数据库、接口和 Streaming 本地管道。

降水缺失值保留为空，不直接补 0。上海、成都的降水数据覆盖率较低，因此年度排名只纳入覆盖率达到 80% 且存在正降水记录的站点。具体统计见 [数据质量说明](DATA_QUALITY.md)。

每个城市只选一个站点，不能代表全省。预测使用历史月均温，8 个城市中有 4 个在测试集上未优于上一年同月的基线，结果仅用于统计分析展示。

## 扩展脚本

`hadoop/` 中的 Mapper/Reducer 已做本地管道测试。Hive 外部表、ORC 汇总查询、MySQL 建表及 Sqoop 导出脚本尚未在真实集群运行。

MySQL 导出密码通过 `WEATHER_DB_PASSWORD` 设置。Django 使用 `DJANGO_SECRET_KEY` 环境变量，未设置时生成本地演示用的临时随机值。

## 数据来源

[NOAA/NCEI Global Summary of the Day](https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/)。如需重新下载样本，在项目根目录运行 `python -m pipeline.fetch_ncei`。
