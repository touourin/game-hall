# DouZero 模型

需要斗地主 AI 时，将官方 `douzero_WP` 模型中的以下三个权重放在本目录：

- `landlord.ckpt`
- `landlord_up.ckpt`
- `landlord_down.ckpt`

再在 `.env` 设置 `INSTALL_DOUZERO_AI=1` 并重新构建。构建过程会生成
`SHA256SUMS`、真实加载全部模型，并把验证通过的权重直接放入应用镜像。本目录中的
权重由 Git 忽略，不会随源码提交，也不会在拉取代码时被覆盖。后续重新构建镜像仍会
使用这些源文件，请不要在首次构建后删除它们。

官方下载说明：https://github.com/kwai/DouZero/blob/main/README.zh-CN.md#评估
