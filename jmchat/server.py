import json
import socket
import threading
import time
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse


class ChatHandler(BaseHTTPRequestHandler):
    messages = []
    message_id = 0
    lock = threading.Lock()

    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _send_json(self, code, obj):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path

            if path == '/api/list':
                with self.lock:
                    self._send_json(200, {
                        'messages': self.messages,
                        'count': len(self.messages)
                    })

            elif path.startswith('/api/message/'):
                try:
                    mid = int(path.split('/')[-1])
                except ValueError:
                    self._send_json(400, {'error': 'Invalid message id'})
                    return
                with self.lock:
                    msg = next((m for m in self.messages if m['id'] == mid), None)
                if msg:
                    self._send_json(200, msg)
                else:
                    self._send_json(404, {'error': 'Message not found'})

            elif path == '/':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"<h1>Chat Server is Running</h1>")

            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            print(f"GET error: {e}")

    def do_POST(self):
        try:
            parsed_path = urlparse(self.path)
            if parsed_path.path == '/api/message':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                username = data.get('username', 'Anonymous')
                message = data.get('message', '')

                if not message:
                    self._send_json(400, {'error': 'Message cannot be empty'})
                    return

                with self.lock:
                    ChatHandler.message_id += 1
                    new_message = {
                        'id': ChatHandler.message_id,
                        'username': username,
                        'message': message,
                        'timestamp': time.time(),
                        'time_str': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.messages.append(new_message)
                    if len(self.messages) > 1000:
                        self.messages = self.messages[-1000:]

                self._send_json(200, {'success': True, 'message': new_message})
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            print(f"POST error: {e}")

    def do_PUT(self):
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path

            if path.startswith('/api/message/'):
                try:
                    mid = int(path.split('/')[-1])
                except ValueError:
                    self._send_json(400, {'error': 'Invalid message id'})
                    return

                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                with self.lock:
                    msg = next((m for m in self.messages if m['id'] == mid), None)
                    if not msg:
                        self._send_json(404, {'error': 'Message not found'})
                        return

                    if 'username' in data:
                        msg['username'] = data['username']
                    if 'message' in data:
                        msg['message'] = data['message']

                self._send_json(200, {'success': True, 'message': msg})
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            print(f"PUT error: {e}")

    def do_DELETE(self):
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path

            if path.startswith('/api/message/'):
                try:
                    mid = int(path.split('/')[-1])
                except ValueError:
                    self._send_json(400, {'error': 'Invalid message id'})
                    return

                with self.lock:
                    before = len(self.messages)
                    self.messages = [m for m in self.messages if m['id'] != mid]
                    after = len(self.messages)

                if before == after:
                    self._send_json(404, {'error': 'Message not found'})
                else:
                    self._send_json(200, {'success': True, 'deleted_id': mid})

            elif path == '/api/messages':
                with self.lock:
                    count = len(self.messages)
                    self.messages.clear()
                self._send_json(200, {'success': True, 'deleted_count': count})
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            print(f"DELETE error: {e}")

    def log_message(self, format, *args):
        pass


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def check_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('0.0.0.0', port))
            return True
        except socket.error:
            return False


class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("郡猫聊天开服工具")
        self.root.geometry("950x700")
        self.root.minsize(800, 600)

        self.httpd = None
        self.server_thread = None
        self.is_running = False

        self.edit_entry = None
        self.edit_item = None
        self.edit_column = None

        status_frame = ttk.LabelFrame(root, text="服务器状态", padding=8)
        status_frame.pack(fill='x', padx=10, pady=5)

        self.status_var = tk.StringVar(value="已停止")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                       foreground="red", font=("Arial", 12, "bold"))
        self.status_label.pack(side='left')

        self.access_var = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.access_var,
                  foreground="green").pack(side='right')

        row1 = ttk.Frame(root)
        row1.pack(fill='x', padx=10, pady=5)
        ttk.Label(row1, text="端口:", width=10).pack(side='left')
        self.port_var = tk.StringVar(value="8080")
        self.port_entry = ttk.Entry(row1, textvariable=self.port_var, width=15)
        self.port_entry.pack(side='left')
        ttk.Button(row1, text="检测端口", command=self.check_port).pack(side='left', padx=10)

        row2 = ttk.Frame(root)
        row2.pack(fill='x', padx=10, pady=5)
        ttk.Label(row2, text="本机IP:", width=10).pack(side='left')
        self.local_ip_var = tk.StringVar(value=get_local_ip())
        ttk.Label(row2, textvariable=self.local_ip_var, foreground="blue").pack(side='left')
        ttk.Button(row2, text="刷新", command=self.refresh_ip).pack(side='left', padx=10)

        btn_frame = ttk.Frame(root, padding=10)
        btn_frame.pack(fill='x', padx=10)

        self.start_btn = ttk.Button(btn_frame, text="启动服务器", command=self.start_server)
        self.start_btn.pack(side='left', padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="停止服务器", command=self.stop_server,
                                    state='disabled')
        self.stop_btn.pack(side='left', padx=5)

        toolbar = ttk.Frame(root)
        toolbar.pack(fill='x', padx=10, pady=5)

        ttk.Button(toolbar, text="刷新", command=self.refresh_messages).pack(side='left', padx=2)
        ttk.Button(toolbar, text="删除选中", command=self.delete_selected).pack(side='left', padx=2)
        ttk.Button(toolbar, text="清空全部", command=self.clear_all).pack(side='left', padx=2)

        ttk.Label(toolbar, text="  搜索:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=20)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.refresh_messages())

        ttk.Label(toolbar, text="(双击单元格可编辑)",
                  foreground="#888").pack(side='right')

        tree_frame = ttk.Frame(root)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('id', 'username', 'message', 'time')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        self.tree.heading('id', text='ID')
        self.tree.heading('username', text='用户名')
        self.tree.heading('message', text='消息内容')
        self.tree.heading('time', text='时间')

        self.tree.column('id', width=50, anchor='center')
        self.tree.column('username', width=120)
        self.tree.column('message', width=470)
        self.tree.column('time', width=150)

        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.tree.bind('<Double-1>', self.on_double_click)

        stat_frame = ttk.Frame(root)
        stat_frame.pack(fill='x', padx=10, pady=5)
        self.msg_count_var = tk.StringVar(value="共 0 条消息")
        ttk.Label(stat_frame, textvariable=self.msg_count_var).pack(side='left')

        self.update_stats()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def check_port(self):
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
            return
        if not (1 <= port <= 65535):
            messagebox.showerror("错误", "端口范围 1-65535")
            return
        if check_port_available(port):
            messagebox.showinfo("检测结果", f"端口 {port} 可用")
        else:
            messagebox.showwarning("检测结果", f"端口 {port} 已被占用")

    def refresh_ip(self):
        ip = get_local_ip()
        self.local_ip_var.set(ip)

    def start_server(self):
        if self.is_running:
            return
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
            return
        if not (1 <= port <= 65535):
            messagebox.showerror("错误", "端口范围 1-65535")
            return
        if not check_port_available(port):
            messagebox.showerror("错误", f"端口 {port} 已被占用")
            return

        try:
            self.httpd = HTTPServer(('0.0.0.0', port), ChatHandler)
        except Exception as e:
            messagebox.showerror("错误", f"创建服务器失败: {e}")
            return

        self.server_thread = threading.Thread(target=self._serve, daemon=True)
        self.server_thread.start()

        self.is_running = True
        ip = get_local_ip()
        self.local_ip_var.set(ip)
        self.access_var.set(f"http://{ip}:{port}")

        self.status_var.set(f"运行中 - 端口 {port}")
        self.status_label.config(foreground="green")
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.port_entry.config(state='disabled')

    def _serve(self):
        try:
            self.httpd.serve_forever()
        except Exception as e:
            print(f"服务器异常: {e}")

    def stop_server(self):
        if not self.is_running:
            return
        try:
            self.httpd.shutdown()
            self.httpd.server_close()
        except Exception as e:
            print(f"停止出错: {e}")

        self.is_running = False
        self.httpd = None
        self.status_var.set("已停止")
        self.status_label.config(foreground="red")
        self.access_var.set("")
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.port_entry.config(state='normal')

    def refresh_messages(self):
        self._commit_edit()

        selected = self.tree.selection()
        selected_id = selected[0] if selected else None

        keyword = self.search_var.get().strip().lower()

        for item in self.tree.get_children():
            self.tree.delete(item)

        with ChatHandler.lock:
            msgs = list(ChatHandler.messages)

        shown = 0
        for m in msgs:
            if keyword:
                if (keyword not in m.get('username', '').lower()
                        and keyword not in m.get('message', '').lower()):
                    continue
            preview = m.get('message', '')
            if len(preview) > 80:
                preview = preview[:80] + '...'
            self.tree.insert('', 'end', iid=str(m['id']), values=(
                m['id'],
                m.get('username', ''),
                preview,
                m.get('time_str', '')
            ))
            shown += 1

        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id)

        self.msg_count_var.set(f"共 {len(msgs)} 条消息，显示 {shown} 条")

    def get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def on_double_click(self, event):
        self._commit_edit()

        region = self.tree.identify('region', event.x, event.y)
        if region != 'cell':
            return

        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)

        if not row_id or not col_id:
            return

        col_index = int(col_id.replace('#', ''))
        col_names = ['id', 'username', 'message', 'time']
        col_name = col_names[col_index - 1]

        if col_name not in ('username', 'message'):
            return

        bbox = self.tree.bbox(row_id, col_id)
        if not bbox:
            return
        x, y, w, h = bbox

        mid = int(row_id)
        with ChatHandler.lock:
            msg = next((m for m in ChatHandler.messages if m['id'] == mid), None)
            if not msg:
                return
            current_value = msg.get(col_name, '')

        self.edit_entry = tk.Entry(self.tree, borderwidth=1, relief='solid')
        self.edit_entry.insert(0, current_value)
        self.edit_entry.select_range(0, 'end')
        self.edit_entry.focus_set()
        self.edit_entry.place(x=x, y=y, width=w, height=h)

        self.edit_item = row_id
        self.edit_column = col_name

        self.edit_entry.bind('<Return>', lambda e: self._commit_edit())
        self.edit_entry.bind('<Escape>', lambda e: self._cancel_edit())
        self.edit_entry.bind('<FocusOut>', lambda e: self._commit_edit())

    def _commit_edit(self):
        if not self.edit_entry:
            return

        entry = self.edit_entry
        item_id = self.edit_item
        col_name = self.edit_column

        try:
            entry.unbind('<FocusOut>')
        except Exception:
            pass

        new_value = entry.get()

        try:
            entry.destroy()
        except Exception:
            pass
        self.edit_entry = None
        self.edit_item = None
        self.edit_column = None

        if not item_id or not col_name:
            return

        mid = int(item_id)
        with ChatHandler.lock:
            msg = next((m for m in ChatHandler.messages if m['id'] == mid), None)
            if not msg:
                return
            old_value = msg.get(col_name, '')
            if new_value == old_value:
                return

            if col_name == 'username':
                msg['username'] = new_value.strip() or ''
            elif col_name == 'message':
                if not new_value.strip():
                    return
                msg['message'] = new_value

        self._update_row(mid)

    def _cancel_edit(self):
        if self.edit_entry:
            try:
                self.edit_entry.unbind('<FocusOut>')
            except Exception:
                pass
            self.edit_entry.destroy()
            self.edit_entry = None
            self.edit_item = None
            self.edit_column = None

    def _update_row(self, mid):
        if not self.tree.exists(str(mid)):
            return
        with ChatHandler.lock:
            msg = next((m for m in ChatHandler.messages if m['id'] == mid), None)
            if not msg:
                return
            preview = msg.get('message', '')
            if len(preview) > 80:
                preview = preview[:80] + '...'
            values = (
                msg['id'],
                msg.get('username', ''),
                preview,
                msg.get('time_str', '')
            )
        self.tree.item(str(mid), values=values)

    def delete_selected(self):
        mid = self.get_selected_id()
        if mid is None:
            messagebox.showinfo("提示", "请先在列表中选择一条消息")
            return

        if not messagebox.askyesno("确认", f"确定删除消息 #{mid} 吗？"):
            return

        with ChatHandler.lock:
            before = len(ChatHandler.messages)
            ChatHandler.messages = [m for m in ChatHandler.messages if m['id'] != mid]
            after = len(ChatHandler.messages)

        if before == after:
            messagebox.showerror("错误", "消息不存在")
        else:
            self.refresh_messages()

    def clear_all(self):
        if not messagebox.askyesno("确认", "确定要清空所有消息吗？此操作不可恢复。"):
            return
        with ChatHandler.lock:
            count = len(ChatHandler.messages)
            ChatHandler.messages.clear()
            ChatHandler.message_id = 0
        self.refresh_messages()

    def update_stats(self):
        try:
            if self.edit_entry is None:
                self.refresh_messages()
        except Exception:
            pass
        self.root.after(2000, self.update_stats)

    def on_close(self):
        if self.is_running:
            if not messagebox.askyesno("确认", "服务器正在运行，确定退出吗？"):
                return
            self.stop_server()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"程序异常: {e}")
        traceback.print_exc()
        input("按回车键退出...")
