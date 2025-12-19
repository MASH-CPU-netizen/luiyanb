from flask import Flask, render_template, request, jsonify
import json
import os
import threading
import queue
import time
app = Flask(__name__)

# 用于持久化的文件（服务启动时加载、运行中实时保存）
COMMENT_FILE = "comments_backup.json"
# 内存存储留言的变量（保持原有逻辑）
COMMENTS = []
# 定义任务队列和线程控制标志
save_queue = queue.Queue()#线程安全的任务队列，queue.Queue为python自带的队列
is_running = True#通过更改is_running值来停止或者运行线程
interval=30;
star_1=time.time();
F=False
star=time.time()
# 后台单线程的任务处理函数：持续从队列取任务执行
def save_worker():
    #is_running！=True结束循环
    global F,star_1
    while is_running:
        try:
            # 阻塞等待队列中的任务，timeout 防止线程一直挂起
            task = save_queue.get(timeout=1)#get的作用是等待一秒后无任务则异常
            save_queue.task_done()  # 标记当前取出的任务已处理完成，需与  get()  配对使用；若后续调用队列的  join()  方法，会等待所有任务都被标记为  done  后再解除阻塞。
            if task == "save":
                star=time.time()
                F = True
            if F and star - star_1 >= interval:
                # 当task为save才进行写的操作
                with open(COMMENT_FILE, "w", encoding="utf-8") as f:
                    json.dump(COMMENTS, f, ensure_ascii=False,
                              indent=2)  # as f  后面是要操作的对象，json.dump模块是将python对象序列化为JSON格式写入文件
                star_1 = time.time()
                F = False
        except queue.Empty:
            star=time.time()
            if F and star - star_1 >= interval:
                # 当task为save才进行写的操作
                with open(COMMENT_FILE, "w", encoding="utf-8") as f:
                    json.dump(COMMENTS, f, ensure_ascii=False,
                              indent=2)  # as f  后面是要操作的对象，json.dump模块是将python对象序列化为JSON格式写入文件
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}]",COMMENTS)
                star_1 = time.time()
                F = False
            continue
            # 兜底处理剩余任务（非递归，安全）
    while not save_queue.empty():
        try:
            task = save_queue.get_nowait()  # 取出并移除剩余任务
            if task == "save":
                with open(COMMENT_FILE, "w", encoding="utf-8") as f:
                    json.dump(COMMENTS, f, ensure_ascii=False, indent=2)
            save_queue.task_done()
        except queue.Empty:
            break

# 启动后台单线程
worker_thread = threading.Thread(target=save_worker, daemon=True)#target=save_worker指定执行函数
worker_thread.start()

# 服务启动时，从文件加载数据到内存变量
def load_comments():
    if os.path.exists(COMMENT_FILE):
        with open(COMMENT_FILE, "r", encoding="utf-8") as f:
            try:
                # 将文件中的数据读取到内存变量COMMENTS
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


# 内存变量变化时，实时将数据写入文件（备份）
def save_comments():
   save_queue.put("save")


# 初始化：服务启动时加载历史留言到内存
COMMENTS = load_comments()


@app.route('/')
def index(): 
    return render_template('index.html', comments=COMMENTS)


@app.route('/api/post-comment', methods=['POST'])
def submit_comment():
    data = request.get_json()
    name = data.get('name', '').strip()
    content = data.get('content', '').strip()

    if not name or not content:
        return jsonify({'status': 'error', 'msg': '姓名和留言内容不能为空！'})
    if len(name) > 10:
        return jsonify({'status': 'error', 'msg': '姓名不能超过10个字符！'})
    if len(content) > 200:
        return jsonify({'status': 'error', 'msg': '留言内容不能超过200个字符！'})

    new_comment = {
        'id': len(COMMENTS) + 1,
        'name': name,
        'content': content
    }
    COMMENTS.insert(0, new_comment)

    # 新增：写入文件备份（实现重启后保留）
    save_comments()

    return jsonify({'status': 'success', 'comment': new_comment})


if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        is_running=False
        save_queue.join()
        worker_thread.join()