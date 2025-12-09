from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 内存存储留言，初始为空列表
COMMENTS = []


@app.route('/')
def index():
    return render_template('index.html', comments=COMMENTS)


# 接口路径修改为 /api/post-comment
@app.route('/api/post-comment', methods=['POST'])
def submit_comment():
    data = request.get_json()
    name = data.get('name', '').strip()
    content = data.get('content', '').strip()

    # 验证逻辑
    if not name or not content:
        return jsonify({'status': 'error', 'msg': '姓名和留言内容不能为空！'})
    if len(name) > 10:
        return jsonify({'status': 'error', 'msg': '姓名不能超过10个字符！'})
    if len(content) > 200:
        return jsonify({'status': 'error', 'msg': '留言内容不能超过200个字符！'})

    # 新增留言
    new_comment = {
        'id': len(COMMENTS) + 1,
        'name': name,
        'content': content
    }
    COMMENTS.insert(0, new_comment)

    return jsonify({'status': 'success', 'comment': new_comment})


if __name__ == '__main__':
    app.run(debug=True)