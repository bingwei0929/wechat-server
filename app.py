import asyncio
import os
import signal
import json
import websockets
from websockets import WebSocketServerProtocol

# 解决Windows本地测试兼容问题（Render服务器无需此代码，但保留不影响）
try:
    from asyncio import WindowsSelectorEventLoopPolicy
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
except ImportError:
    pass

connected_clients = set()

async def handle_client(websocket: WebSocketServerProtocol):
    connected_clients.add(websocket)
    print(f"📥 新客户端连接，当前在线：{len(connected_clients)}人")

    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"📩 收到消息：{data}")
            # 转发消息给其他客户端
            for client in connected_clients:
                if client != websocket:
                    await client.send(json.dumps(data))
    except websockets.exceptions.ConnectionClosed:
        print("⚠️ 客户端断开连接")
    finally:
        connected_clients.remove(websocket)
        print(f"📤 客户端已断开，当前在线：{len(connected_clients)}人")

async def main():
    # 关键：使用Render提供的环境变量端口（必须配置，否则部署失败）
    port = int(os.environ.get("PORT", 8765))  # 本地测试默认8765，Render会自动分配端口
    # 绑定0.0.0.0允许公网访问（Render要求）
    async with websockets.serve(handle_client, "0.0.0.0", port):
        print(f"🚀 服务启动，端口：{port}")
        # 处理Render的关闭信号（确保优雅退出）
        loop = asyncio.get_running_loop()
        stop_signal = loop.create_future()
        loop.add_signal_handler(signal.SIGTERM, stop_signal.set_result, None)
        await stop_signal  # 保持服务运行

if __name__ == "__main__":
    asyncio.run(main())