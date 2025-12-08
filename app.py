from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
# 留言数据存储文件（自动创建）
DATA_FILE = "comments.json"


# 初始化数据文件（首次运行创建）
def init_data_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


# 读取所有留言
def get_all_comments():
    init_data_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# 新增留言
def add_comment(name, content):
    comments = get_all_comments()
    new_comment = {
        "name": name,
        "content": content,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 格式化时间
    }
    comments.insert(0, new_comment)  # 新留言插在最前面
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    return new_comment


# 主页：渲染留言板页面
@app.route("/")
def index():
    comments = get_all_comments()
    return render_template("index.html", comments=comments)


# 接口：接收前端提交的留言（AJAX 调用）
@app.route("/api/post-comment", methods=["POST"])
def post_comment():
    data = request.get_json()
    name = data.get("name", "").strip()
    content = data.get("content", "").strip()

    # 简单验证：姓名和留言不能为空
    if not name or not content:
        return jsonify({"status": "error", "msg": "姓名和留言不能为空！"})

    # 新增留言并返回结果
    new_comment = add_comment(name, content)
    return jsonify({"status": "success", "comment": new_comment})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)