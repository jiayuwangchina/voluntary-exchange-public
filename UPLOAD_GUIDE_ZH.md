# GitHub 上传说明

本包包含匿名正文、完整附录、LaTeX 源文件、官方模板文件、数据和复现代码。
正文为34页，附录为45页，摘要99词。作者、单位、邮箱和致谢均未加入。

## 网页上传

1. 解压文件包，进入 `voluntary-exchange` 文件夹。
2. 在 GitHub 新建仓库，例如 `voluntary-exchange`。仓库描述可用：
   `Anonymous manuscript and replication materials for voluntary exchange under separate public accounts.`
3. 上传该文件夹内的全部文件及子文件夹，保留目录结构。
4. 检查首页能显示 README，并能打开两份 PDF。

如需用于盲审，个人公开仓库会显示账号身份，应选择符合审稿安排的访问方式。
本文件包没有替您创建仓库或公开发布。

## 使用 Git 上传

在解压后的文件夹内运行以下命令。将远程地址替换为您实际创建的仓库地址。

```bash
git init
git add .
git commit -m "Add anonymous manuscript and replication materials"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

提交记录会使用您本机的 Git 用户设置。本包没有配置作者姓名、邮箱或 Git 身份。

## 修改与重新编译

安装完整 TeX Live 或 MiKTeX、Python 和 Poppler 后，在仓库根目录运行：

```bash
python build.py
```

两份 `.tex` 都已包含参考文献。官方模板不使用 `xr-hyper`，跨文档引用采用
明确编号；编译脚本通过 `%<xref:...>` 注释自动刷新这些编号，请保留注释。
定理已按官方样式连续编号，附录定理采用 `A.1`、`A.2` 等前缀加连续编号。

不要将旧版本的 `_labels.aux` 或编辑回复、投稿信混入这个匿名包。
完整附录保留全部证明和扩展；投稿前仍需在期刊当前投稿页面确认补充材料篇幅上限。
