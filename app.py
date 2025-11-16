import asyncio
import json
import os
import websockets
from websockets import WebSocketServerProtocol

# 解决Windows系统事件循环兼容问题（Render 是Linux环境，此代码仍兼容）
if os.name == 'nt':  # 仅在Windows系统生效
    if asyncio.get_event_loop_policy()._loop_factory.__name__ == 'ProactorEventLoop':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 存储所有连接的客户端
connected_clients = set()


async def handle_client(websocket: WebSocketServerProtocol):
    """处理客户端连接和消息转发"""
    connected_clients.add(websocket)
    print(f"📥 新客户端连接，当前在线：{len(connected_clients)}人")

    try:
        async for message in websocket:
            # 解析消息并广播
            try:
                data = json.loads(message)
                print(f"📩 收到消息：{data}")
                # 转发给其他客户端
                for client in connected_clients:
                    if client != websocket:
                        await client.send(json.dumps(data))
            except json.JSONDecodeError:
                print(f"❌ 消息格式错误：{message}")
            except Exception as e:
                print(f"❌ 消息处理错误：{e}")
    except websockets.exceptions.ConnectionClosed:
        print("🔌 客户端主动断开连接")
    except Exception as e:
        print(f"❌ 客户端处理错误：{e}")
    finally:
        connected_clients.remove(websocket)
        print(f"📤 客户端断开，当前在线：{len(connected_clients)}人")


async def start_server():
    """启动WebSocket服务器（适配Render动态端口）"""
    try:
        # 关键修改：使用Render提供的环境变量端口，默认本地测试用8765
        port = int(os.environ.get("PORT", 8765))
        # 监听0.0.0.0，允许外部访问（Render要求）
        async with websockets.serve(handle_client, "0.0.0.0", port):
            print(f"🚀 服务器已启动，监听端口：{port}")
            await asyncio.Future()  # 保持服务器运行
    except OSError as e:
        if "address already in use" in str(e):
            print(f"❌ 端口被占用，请关闭占用程序或修改端口")
        else:
            print(f"❌ 服务器启动失败：{e}")


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\n⏹️ 服务器已手动关闭")