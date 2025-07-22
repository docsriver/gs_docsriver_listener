# gs_docsriver_listener
Позволяет работать с ps и pdf файлами через http api

# Установка
* Скопировать `gs_docs_river_listener.py` в `/opt/compose/docsriver_scripts/`
* Скопировать `gs_docsriver_listener.service` в `/etc/systemd/system`

# Запуск
Чтобы запустить сервис:
```shell
sudo systemctl start gs_docsriver_listener.service
```

Чтобы включить автозапуск при старте системы:
```shell
sudo systemctl enable gs_docsriver_listener.service
```

Посмотреть статус:
```shell
sudo systemctl status gs_docsriver_listener.service
```

Посмотреть логи:
```shell
sudo journalctl _SYSTEMD_UNIT=gs_docsriver_listener.service
```

Чтобы остановить:
```shell
sudo systemctl stop gs_docsriver_listener.service
```

Чтобы отключить автозапуск при старте системы:
```shell
sudo systemctl disable gs_docsriver_listener.service
```
