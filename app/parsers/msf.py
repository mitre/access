import json

from app.utility.base_parser import BaseParser


class Parser(BaseParser):

    def parse(self, blob, data_svc, **kwargs):
        print(blob)
        json_output = self.load_json(blob)
        for msf_ability in json_output:
            print(msf_ability)
        return []