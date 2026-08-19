# ModernWMS & PartDB Unified Ecosystem Architecture

## 1. System Overview

The **ModernWMS & PartDB Ecosystem** is a multi-tier, hybrid inventory and warehouse management platform. It synchronizes engineering electronic component inventory (PartDB) with enterprise warehouse supply-chain workflows (ModernWMS), providing multi-channel access (Web UI, Touch/Tablet Kiosk, Rugged Telnet Terminals, and Native Android App).

```mermaid
graph TD
    subgraph Client Layer
        Browser[Web Browser / PWA<br>Port 7681]
        Scanner[Handheld Barcode Scanner / Telnet<br>Port 2323 / 23]
        Tablet[Tablet / Touch Screen Kiosk<br>Port 7681 / 7682]
        Android[Android Native App<br>ModernWMS_Touch_Suite.apk]
        CLI[Server Admin / Host CLI<br>modernwms / manage-users]
    end

    subgraph Gateway Layer
        WebProxy[Gateway Web Proxy<br>web_proxy.py : 7681]
        TTYD[Touch Terminal Engine<br>ttyd : 7682]
        TelnetDaemon[Telnet PTY Daemon<br>telnet_server.py : 2323]
    end

    subgraph Application & Control Suite
        TUI[Enterprise Control Suite TUI<br>modernwms_tui.py]
        UserMgr[Enterprise User & Security Manager<br>user_manager.py]
        ReceiveStock[ASN Stock Receiving Engine<br>receive_stock.py]
        SyncEngine[PartDB -> ModernWMS Sync Engine & API<br>sync_service.py : 8082]
    end

    subgraph Core Database & Server Services
        PartDB[(PartDB SQLite Database<br>app.db / Port 8081)]
        ModernWMS[(ModernWMS SQLite Database<br>wms.db / Port 80)]
        Prometheus[Prometheus Monitoring<br>Port 9091]
        Grafana[Grafana Dashboards<br>Port 3000]
    end

    Browser --> WebProxy
    Tablet --> WebProxy
    Android --> WebProxy
    WebProxy --> TTYD
    TTYD --> TUI
    Scanner --> TelnetDaemon
    TelnetDaemon --> TUI
    CLI --> TUI
    CLI --> UserMgr
    CLI --> ReceiveStock

    TUI --> UserMgr
    TUI --> PartDB
    TUI --> ModernWMS
    UserMgr --> PartDB
    UserMgr --> ModernWMS
    ReceiveStock --> ModernWMS

    SyncEngine --> PartDB
    SyncEngine --> ModernWMS
    Prometheus -->|Scrapes /metrics| SyncEngine
    Grafana -->|Queries Prometheus| Prometheus
