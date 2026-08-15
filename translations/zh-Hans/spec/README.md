<!-- dsx-translation
source: spec/README.md
source_sha256: f4438fb7fd381a5dfd23830ac1b4677c15768622f1048372c618a5cbf3470c9a
language: zh-Hans
translated: 2026-08-16
translator: machine, unreviewed
-->

> <!-- dsx-governing-language -->
> **本译文仅供参考，不具规范效力。**
> 本规范以**英文文本为唯一权威版本**。译文与英文文本不一致时，**以英文文本为准**。
> 英文原文：[`spec/README.md`](../../../spec/README.md)
>
> *This translation is informative, not normative. The English text is the sole
> authoritative version of this specification; where this translation and the
> English text differ, the English text governs.*

# DSX 规范 — v0.1-draft（草案）

**状态：** 草案。尚不稳定。公开发布以供评审。
**日期：** 2026-08-15

| # | 章节 | 状态 |
|---|---|---|
| 1 | [概述与符合性模型](../../../spec/01-overview.md) | 草案 |
| 2 | [容器与清单](../../../spec/02-container.md) | 草案 |
| 3 | [坐标、高度与时间](../../../spec/03-coordinates-and-time.md) | 草案 |
| 4 | [轨迹、灯光与规范性采样](../../../spec/04-trajectories-and-light.md) | 草案 |
| 5 | [设备配置文件（`.dsxp`）](../../../spec/05-device-profiles.md) | 草案 |
| 6 | [载荷与执行器](../../../spec/06-payloads-and-actuators.md) | 草案 |
| 7 | [安全与终止](../../../spec/07-safety-and-termination.md) | 草案 |
| 8 | [扩展、配置文件与版本管理](../../../spec/08-extensions-and-versioning.md) | 草案 |
| 9 | [符合性](../../../spec/09-conformance.md) | 提纲 |
| 10 | [波次、架次、轮换与连续运行](../../../spec/10-waves-and-rotation.md) | 草案 |
| A | [未决问题](../../../spec/A-open-questions.md) | 持续更新（不翻译） |
| B | [已观察到的第三方格式](../../../spec/B-observed-formats.md) | 持续更新 |

## 权威语言

**英文是本规范唯一的权威语言。** 译文仅为方便阅读而发布，**具有参考性质，绝不具备规范
效力**。当译文与英文文本存在差异时 —— 无论是措辞、符合性关键词还是数值 —— **以英文文本
为准，读者必须 (MUST) 依据英文文本解决该问题。**

这并非套话。符合性关键词承载着安全义务：若某种语言把 `MUST`（必须）译成了建议，使用该语言
的实现者就会开发出一个面向飞行器的工具，其中省略了必需的检查，却自认为符合规范。上述规则的
存在，正是为了让这类缺陷始终能够依据唯一文本得到裁定，而不是在两份文本之间争论。

因此，每个译文页面都会注明其所依据的英文提交版本，并且一旦英文原文发生变动，
`conformance/check_translations.py` 就会将该译文标记为**过期（stale）**。过期的译文是一个
有名有姓的已知缺陷，而不是一个无声的缺陷。参见 [`TRANSLATIONS.md`](../../../TRANSLATIONS.md)。

## 符合性关键词

关键词 **MUST**（必须）、**MUST NOT**（禁止）、**REQUIRED**（必需）、**SHALL**（应当）、
**SHALL NOT**（不得）、**SHOULD**（宜）、**SHOULD NOT**（不宜）、**MAY**（可）和
**OPTIONAL**（可选）的解释遵循 BCP 14（RFC 2119 / RFC 8174），且仅在其以全大写形式出现时
适用。

> **关于关键词翻译的说明：** 括号中的英文术语不是装饰。这些关键词是专业术语而非普通词汇；
> 依据英文文本核对的读者需要在英文原文中找到完全相同的词。译文中首次出现时必须 (MUST) 保留
> 英文原词。
