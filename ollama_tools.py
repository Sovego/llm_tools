import ollama
import logging
class OllamaWrapper:
    def __init__(self, model: str):
        self.model = model
        self.client = ollama.AsyncClient()
        self.tools = {}
        self.messages = []

    def add_tool(self, name, func, description, parameters):
        """
        Adds a tool to the OllamaWrapper instance.

        This method allows for easy addition of custom functions to be used with the Ollama model.

        This method accepts a name for the tool, a function that can be called to process the user's query,
        a description of the tool, and a list of parameters that the function expects.
        Parameters:
        - name (str): The name for the tool.
        - func (function): The function to be called when the tool is used.
        - description (str): A description of the tool.
        - parameters (list): A list of parameters that the function expects.
        Returns:
        None
        """
        self.tools[name] = {
            "function": func,
            "description": description,
            "parameters": parameters,
        }
        logging.debug(f"Added tool: {name}")


    def get_ollama_tools(self) -> list:
        """
        Retrieves a list of tools that can be used with the Ollama model.

        This method iterates through the tools stored in the OllamaWrapper instance
        and constructs a list of dictionaries, each representing a tool. Each dictionary
        contains the tool's name, description, and parameters.

        Returns:
        list: A list of dictionaries, where each dictionary represents a tool.
        """
        ollama_tools = []
        for name, tool in self.tools.items():
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            })
        logging.debug(f"Available Ollama tools: {ollama_tools}")
        return ollama_tools


    
    async def ask(self, user_query):
        """
        Asynchronously asks a question to the Ollama model, utilizing any available tools.

        Attributes:
        - user_query (str): The question to be asked to the Ollama model.

        Returns:
        str: The response from the Ollama model, including any tool responses.
        """
        self.messages.append({"role": "user", "content": user_query})
        response = await self.client.chat(
            model=self.model,
            messages=self.messages,
            tools=self.get_ollama_tools()
        )
        self.messages.append(response['message'])
        logging.debug(f"Ollama response: {response['message']}")
        tool_calls = response['message'].get('tool_calls', [])
        results = {}
        logging.debug(f"Tool calls: {tool_calls}")
        # Обработка вызовов инструментов
        for tool in tool_calls:
            tool_name = tool['function']['name']
            tool_args = tool['function']['arguments']
            if tool_name in self.tools:
                logging.debug(f"Invoking tool: {tool_name} with args: {tool_args}  ")
                tool_func = self.tools[tool_name]['function']
                # Вызов инструмента с аргументами
                tool_result = tool_func(**tool_args)
                results[tool_name] = tool_result

                # Добавление результата инструмента в историю сообщений
                self.messages.append({
                    'role': 'tool',
                    'content': tool_result,
                })

        # Отправка результатов обратно в модель для получения окончательного ответа
        final_response = await self.client.chat(model=self.model, messages=self.messages)
        return final_response['message']['content']
