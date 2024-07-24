import os
import gspread

from oauth2client.service_account import ServiceAccountCredentials


class SheetAPI:

    def __init__(self, key_tb: str):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        current_dir = os.path.dirname(__file__)
        credentials_path = os.path.join(current_dir, "Your_Credentials.json") # TODO: Change
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scope
        )
        gc = gspread.authorize(credentials)
        self.spreadsheet = gc.open_by_key(key_tb)

    def read(self, list_name: str, column: int) -> list[str]:
        worksheet = self.spreadsheet.worksheet(list_name)
        data = worksheet.col_values(column)[1:]

        return data

    def write(self, list_name: str, range_tb: str, data: list) -> (bool, str):
        try:
            worksheet = self.spreadsheet.worksheet(list_name)

            update_data = []
            for entry in data:
                for store_name, link in entry.items():
                    row = [store_name, link]
                    update_data.append(row)

            worksheet.update(range_name=range_tb, values=update_data)
            return True, "Successfully"

        except Exception as e:
            return False, str(e)


if __name__ == "__main__":
    print("Sheet repository api!")

