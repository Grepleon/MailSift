import json, os

class Saves:
    def __init__(self, file, create_file=False):
        if create_file:
            file_path = file
            with open(file_path, 'w') as File:
                File.write("[]")


        self.file = file
        self.loaded_data:dict|list = self._open()

    def _open(self):
        with open(self.file, "r", encoding="utf-8") as file:
            self.loaded_data = json.load(file)
        return self.loaded_data

    def open_player(self, name):
        return self.loaded_data[name]

    def save_file(self, data:dict|list):
        with open(self.file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        self.loaded_data = data

    def save(self):
        with open(self.file, "w", encoding="utf-8") as file:
            json.dump(self.loaded_data, file, ensure_ascii=False, indent=4)

    def update_player(self, name:str, data:dict):
        self.loaded_data[name] = data
        self.save()
