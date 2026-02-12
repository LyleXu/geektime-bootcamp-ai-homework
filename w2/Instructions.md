# Instructions

## constitution

这是针对 ./w2/db_query 项目的：

- 使用 Ergonomic Python 风格来编写代码， 前端使用typescript
- 前后端都要有严格的类型标注
- 使用pydantic来定义数据模型
- 所有后端生成的json数据，使用camelCase格式。
- 不需要authentication, 任何用户都可以使用。


## 基本思路

这是一个数据库查询工具，用户可以添加一个DB URL， 系统会连接到数据库，获取数据库的metadata， 然后数据库中的table和view的信息展示出来，然后用户可以自己输入sql 查询，也可以通过自然语言来生成sql查询。

基本想法：
- 数据库连接字符串和数据库的metadata都会存储到sqlite数据库中。我们可以根据postgres的功能来查询系统中的表和试图的信息，然后用LLM来将这些信息转换成json格式，然后存储到sqlite数据库中。这个信息以后可以复用。
- 当用户使用LLM来生成sql查询时，我们可以把系统中的表和视图的信息作为context传递给LLM，然后LLM会根据这些信息来生成sql查询。
- 任何输入的sql语句，都需要经过sqlparser解析，确保语法正确，并且仅包含select语句。如果语法不正确，需要给出错误信息。
   - 如果查询不包含limit子句，则默认添加limit 1000 子句。
- 输出格式是json， 前端将其组织成表格，并显示出来。

后端使用Python (uv) / FastAPI / sqlglot / openai sdk 来实现。
前端使用 React / refine 5 / tailwind / ant design 来实现。 sql editor使用 monaco editor 来实现。

OpenAI API key 在环境变量OPENAI_API_KEY中。数据库连接和metadata 存储在 sqlite数据库中，放在~/.db_query/db_query.db中。
//
后端API 需要支持cors, 允许所有 origin。 大致API 如下:
```
# 获取所有已存储的数据库
GET /api/v1/dbs

# 添加一个数据库
PUT /api/v1/dbs/{name}
{
    "url": "postgres://postgres:postgres@localhost:5432/postgres"
}

# 获取一个数据库metadata
GET /api/v1/dbs/{name}

# 查询某个数据库的信息
POST /api/v1/dbs/{name}/query
{
    "sql": "select * from users"

}

# 根据自然语言生成sql
POST /api/v1/dbs/{name}/query/natural
{
    "prompt": "查询用户表的所有信息"
}
```

## 测试

在w2/db_query下撰写PowerShell script来完成基本工作，另外生成w2/db_qeury/fixtures/test.rest,使用vscode rest client来测试所有API.

show database page 使用这样的界面完成
![alt text](image.png)


## 优化 UI
按照 apple website 的设计风格， think ultra hard, 优化UI 和 UX

## 前端风格
使用style.md中的风格，学习 ./site中token的定义，优化整体的UI和UX

## 侧边栏

侧边栏目前用途不大，可以放所有已有的数据库，并且把添加数据库，删除已有的数据库的功能放在侧边栏。侧边栏使用新的token风格。然后主页直接显示第一个数据库的metadata信息和查询界面，这样用户可以减少一次点击进入到database ddisplay页面。一个页面囊括所有功能。

仔细阅读 ./w2/db_query 下面的代码，然后运行后端和前端，根据@w2/db_query/fixtures/test.rest 用curl 测试后端已实现的路由；然后用playwright 开前端测试，任何测试问题，think ultra hard and fix

## db migration and unit test
