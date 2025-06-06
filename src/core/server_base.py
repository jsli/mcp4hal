import inspect
from abc import ABC
from typing import Optional

from fastapi import FastAPI
from mcp.server import FastMCP


class McpServerBase(ABC):
    _root_app: FastAPI

    mcp_server: FastMCP

    server_type: str = 'streamable_http'
    '''streamable_http, sse'''

    base_url: str
    '''外部server的完整url，本地server等同于mount_path'''

    name: str

    description: str

    mount_path: str

    ignore_method = ['mount', '__init__', 'info', '_mount_tools']

    @classmethod
    def mount(cls,
        app: FastAPI,
        mount_path: str,
        base_url: Optional[str] = '',
    ):
        mcp_server = FastMCP(cls.name, json_response=True)
        mcp_server.settings.debug = True
        mcp_server.settings.log_level = "DEBUG"

        if cls.server_type == 'sse':
            mcp_server.settings.sse_path = '/'
            mcp_server.settings.message_path = '/messages/'
            app.mount(f'{mount_path}', app=mcp_server.sse_app(), name=f'{cls.name}')
        elif cls.server_type == 'streamable_http':
            mcp_server.settings.streamable_http_path = '/'
            app.mount(f'{mount_path}', app=mcp_server.streamable_http_app(), name=f'{cls.name}')
        else:
            raise Exception(f'unknown server transport type: [{cls.server_type}], must be one of ["sse", "streamable_http"]')

        service = cls(server=mcp_server, base_url=base_url, mount_path=mount_path)
        return service

    def __init__(self, server: FastMCP, mount_path: str, base_url: str = None):
        self.mcp_server = server
        self.mount_path = mount_path
        self.base_url = base_url[:-1] if base_url.endswith('/') else base_url

        self._mount_tools()

    def info(self):
        base_url = self.base_url[:-1] if self.base_url.endswith('/') else self.base_url
        return {
            "name": self.name,
            "type": self.server_type,
            "url": f'{base_url}{self.mount_path}',
            "description": self.description,
        }

    def _mount_tools(self):
        """调用mcp sdk，添加可以被调用的tool"""
        methods = inspect.getmembers(self.__class__, predicate=inspect.isfunction)
        for method in methods:
            method_name = method[0]
            method_fn = method[1]
            if method_name not in self.ignore_method:
                docstring = inspect.getdoc(method_fn)
                # from docstring_parser import parse
                # parsed = parse(docstring)
                # print(f'add tool --------- {method_name}')
                # for param in parsed.params:
                #     print(f"Parameter: {param.arg_name}, Type: {param.type_name}, Desc: {param.description}")
                # if parsed.returns:
                #     print(f"Returns: Type: {parsed.returns.type_name}, Desc: {parsed.returns.description}")
                self.mcp_server.add_tool(fn=method_fn, name=method_name, description=docstring)
