# Gremlin-ShadTail-Trader Structure

```text
•
├── .git
│   ├── branches
│   ├── hooks
│   │   ├── applypatch-msg.sample
│   │   ├── commit-msg.sample
│   │   ├── post-update.sample
│   │   ├── pre-applypatch.sample
│   │   ├── pre-commit.sample
│   │   ├── pre-merge-commit.sample
│   │   ├── pre-push.sample
│   │   ├── pre-rebase.sample
│   │   ├── pre-receive.sample
│   │   ├── prepare-commit-msg.sample
│   │   ├── push-to-checkout.sample
│   │   └── update.sample
│   ├── info
│   │   └── exclude
│   ├── logs
│   │   ├── refs
│   │   │   ├── heads
│   │   │   │   └── master
│   │   │   └── remotes
│   │   │       └── origin
│   │   │           ├── HEAD
│   │   │           └── master
│   │   └── HEAD
│   ├── objects
│   │   ├── 02
│   │   │   └── 88337422bdb29a59a8292e723823602a9efaba
│   │   ├── 1a
│   │   │   └── b74923e9116f1d8196cd7bb4d44fc50f2a54e1
│   │   ├── 2c
│   │   │   └── ee0c2d1acc4f4a66b83b0432b6d5c42f86a740
│   │   ├── 41
│   │   │   └── 088c9dfefedbf1c3b439e8f7092c0a58e019a0
│   │   ├── b4
│   │   │   └── a25247688d087d0eace88a9275d85bd5ee874a
│   │   ├── c1
│   │   │   └── 418dcf28c546eadc27e8584a29f4818214541c
│   │   ├── f5
│   │   │   └── 69ef90ccac70982d549f37b8dc022de71e0e1b
│   │   ├── f9
│   │   │   └── f63787cd5ee60c50b761db6458773e83f7d7c8
│   │   ├── info
│   │   └── pack
│   │       ├── pack-b39c8e4d3d2d1a2e382bb342e0a3099da50d5280.idx
│   │       └── pack-b39c8e4d3d2d1a2e382bb342e0a3099da50d5280.pack
│   ├── refs
│   │   ├── heads
│   │   │   └── master
│   │   ├── remotes
│   │   │   └── origin
│   │   │       ├── HEAD
│   │   │       └── master
│   │   └── tags
│   ├── COMMIT_EDITMSG
│   ├── FETCH_HEAD
│   ├── HEAD
│   ├── ORIG_HEAD
│   ├── config
│   ├── description
│   ├── index
│   └── packed-refs
├── backend
│   ├── Gremlin_Trade_Core
│   │   ├── Gremlin_Trader_Strategies
│   │   │   ├── .gitkeep
│   │   │   ├── __init__.py
│   │   │   ├── penny_stock_strategy.py
│   │   │   ├── recursive_scanner.py
│   │   │   └── strategy_manager.py
│   │   ├── Gremlin_Trader_Tools
│   │   │   ├── Financial_Agent
│   │   │   │   └── tax_estimator.py
│   │   │   ├── Memory_Agent
│   │   │   │   └── base_memory_agent.py
│   │   │   ├── Rule_Set_Agent
│   │   │   │   ├── rule_set_agent.py
│   │   │   │   └── rules_engine.py
│   │   │   ├── Run_Time_Agent
│   │   │   │   ├── runtime_agent.py
│   │   │   │   └── stock_scraper.py
│   │   │   ├── Service_Agents
│   │   │   │   ├── market_data_service.py
│   │   │   │   └── simple_market_service.py
│   │   │   ├── Strategy_Agent
│   │   │   │   ├── signal_generator.py
│   │   │   │   └── strategy_agent.py
│   │   │   ├── Timing_Agent
│   │   │   │   └── market_timing.py
│   │   │   ├── Tool_Control_Agent
│   │   │   │   ├── portfolio_tracker.py
│   │   │   │   └── tool_control_agent.py
│   │   │   ├── Trade_Agents
│   │   │   │   ├── IBKR-API.trader.py
│   │   │   │   └── Kalshi-API.trader.py
│   │   │   ├── Agents_out.py
│   │   │   └── README.md
│   │   ├── config
│   │   │   ├── Gremlin_Trade_Config
│   │   │   │   ├── memory.json
│   │   │   │   ├── trade_agents.config
│   │   │   │   └── trade_strategy.config
│   │   │   ├── Gremlin_Trade_Logs
│   │   │   │   └── Agents.out
│   │   │   ├── Agent_in.py
│   │   │   └── FullSpec.config
│   │   ├── plugins
│   │   │   ├── grok
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── agent_coordinator.py
│   │   └── globals.py
│   ├── Gremlin_Trade_Memory
│   │   ├── vector_store
│   │   │   ├── chroma.sqlite3
│   │   │   ├── git.keep
│   │   │   └── metadata.db
│   │   ├── __init__.py
│   │   └── embedder.py
│   ├── __init__.py
│   ├── build-log.txt
│   ├── install-log.txt
│   ├── main.py
│   ├── pyproject.toml
│   └── server.py
├── electron
│   ├── main.js
│   ├── main.js.backup
│   └── preload.js
├── frontend
│   ├── bin
│   │   ├── gopls
│   │   └── staticcheck
│   ├── pkg
│   │   ├── mods
│   │   ├── sumdb
│   │   └── .gitikeep
│   ├── src
│   │   ├── components
│   │   │   ├── ui
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── switch.tsx
│   │   │   │   └── tabs.tsx
│   │   │   ├── AgentManager.tsx
│   │   │   ├── DC4306F4-2AF9-4439-8861-BEAA3018EB3A.png
│   │   │   ├── Dashboard.tsx
│   │   │   ├── GrokChat.tsx
│   │   │   ├── IMG_3501.jpeg
│   │   │   ├── Settings.tsx
│   │   │   └── SourceEditor.tsx
│   │   ├── pages
│   │   │   └── index.astro
│   │   ├── styles
│   │   │   └── globals.css
│   │   ├── types
│   │   │   └── electron.d.ts
│   │   ├── utils
│   │   │   ├── cn.ts
│   │   │   └── logger.ts
│   │   └── env.d.ts
│   ├── astro.config.mjs
│   ├── package-lock.json
│   ├── package.json
│   ├── shadcn.config.js
│   └── tailwind.config.cjs
├── resources
│   ├── dmg-background.png
│   ├── entitlements.mac.plist
│   ├── icon.icns
│   ├── icon.ico
│   └── icon.png
├── scripts
│   ├── GremlinTrader.desktop
│   ├── bootstrap.js
│   ├── install-all
│   ├── launch-gremlin-trader.sh
│   ├── postpack.js
│   └── prebuild.js
├── .gitignore
├── .hintrc
├── README.md
├── Structure.md
├── __init__.py
├── package-lock.json
└── package.json

60 directories, 128 files
```
