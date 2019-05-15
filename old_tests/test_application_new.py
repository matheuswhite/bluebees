import sys
sys.path.append('C:\\Users\\tenor\\OneDrive\\Documentos\\bluebees\\')

from client.application.application_data import ApplicationData
from client.data_paths import base_dir, app_dir


if __name__ == "__main__":
    app1 = ApplicationData(name='ayna-app', key=b'1234', nodes=['vsx01',
                                                                'vsx02',
                                                                'vsx05'])

    app1.save()

    app2 = ApplicationData.load(app1.filename)

    assert app2 == app1

    print(app2)
