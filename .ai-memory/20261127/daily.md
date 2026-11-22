
## [10:55] - [代码审查+修复]: 四技能全面自查 powerwiki 逻辑与界面

- **文件**: build_site.py（+3 行手机端 SCROLL 收起）、character/yutu.html（构建产物）、CHANGELOG.md（第九批）、service-worker.js（pw-v97）
- **决策**: 审计阶段只读不改码；3 处初判失败经复核均为测试脚本选择器写错（目录项是 button、切换器需先展开、阅读记忆按百分比正确），非站点 bug；唯一真问题 P2 用最小 CSS 覆盖修，不侵入 React bundle
- **验证**: audit 全过+构建幂等；30 页次浏览器 0 溢出/0 破图/0 错误；交互实测全通过；修复后 390 隐藏 SCROLL/1440 保留/截图确认干净
