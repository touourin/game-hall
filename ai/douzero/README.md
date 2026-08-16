# DouZero WP 模型

本目录固定保存 DouZero 官方发布的 `douzero_WP` 三角色预训练模型：

- `landlord.ckpt`：地主
- `landlord_up.ckpt`：地主上家
- `landlord_down.ckpt`：地主下家

模型来源于 [DouZero 官方评估资源][upstream-models]，三个文件作为同一套模型纳入
版本控制；`SHA256SUMS` 固定其内容，不能只替换其中一个角色。权重与 CPU 架构无关，
`amd64` 和 `arm64` 构建共用同一套文件。

在 `.env` 设置 `INSTALL_DOUZERO_AI=1` 后构建即可启用。Docker 会先校验仓库中的
清单，再把权重复制到镜像，并通过正式 worker 真实加载三个模型。运行容器不挂载宿主
机目录，新服务器拉取完整仓库后不需要再手工下载或复制权重。

更新模型时，应同时替换三个角色文件，并重新生成、检查校验清单：

```bash
python backend/app/ai/douzero_models.py ai/douzero
```

DouZero 项目代码采用 Apache-2.0 许可证；模型版权与适用条款以官方发布说明为准。

[upstream-models]: https://github.com/kwai/DouZero/blob/main/README.zh-CN.md#评估
