# Integrated technical, business, data, IT and user manual

Version 1.0 — 22 October 2026. The authoritative 8-page LaTeX source and compiled PDF are stored in the established OneDrive project folder.

- [Full LaTeX source (.tex)](https://onedrive.live.com?cid=BDD18D98B3B583D5&id=BDD18D98B3B583D5!s5278308d6b9d434784f0fd6baf00d02b)
- [Compiled PDF](https://onedrive.live.com?cid=BDD18D98B3B583D5&id=BDD18D98B3B583D5!s76609875c9fd44fba5d4fa2f8843d1df)

The document covers technical thermal/psychrometric and hourly AC-PV optimization models, business case and NPV, data dictionary and relational schema, current versus target IT architecture, proposed APIs, security, user instructions, testing, limitations and roadmap. Current `app.py` is a research simulator with synthetic weather, not an approved controller.

Build locally after downloading the linked source:

```bash
pdflatex -interaction=nonstopmode Relay_Room_Technical_Business_Data_IT_User_Manual.tex
pdflatex -interaction=nonstopmode Relay_Room_Technical_Business_Data_IT_User_Manual.tex
```
