import json

file_path = "enviro/fixtures/custom_html_block.json"
with open(file_path) as f:
	text = f.read()

# Replace wrapper
text = text.replace(
	".inv-dash-wrapper { font-family: 'Inter', sans-serif; background: #fff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }",
	".inv-dash-wrapper { display: flex; flex-direction: column; height: calc(100vh - 140px); font-family: 'Inter', sans-serif; background: #fff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }",
)

# Replace header
text = text.replace(
	".inv-header { display: flex; flex-direction: column; gap: 15px; margin-bottom: 25px; }",
	".inv-header { display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px; flex-shrink: 0; }",
)

# Replace table container
text = text.replace(
	".inv-table-container { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 12px; }",
	".inv-table-container { flex: 1; overflow-y: auto; overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 12px; }",
)

# Replace table th
text = text.replace(
	".inv-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 13px; text-align: center; padding: 12px 8px; border-bottom: 2px solid #e2e8f0; }",
	".inv-table th { position: sticky; top: 0; z-index: 10; background: #f8fafc; color: #475569; font-weight: 600; font-size: 13px; text-align: center; padding: 12px 8px; border-bottom: 2px solid #e2e8f0; box-shadow: 0 2px 2px -1px rgba(0,0,0,0.1); }",
)

# Replace filter bar
text = text.replace(
	".inv-filter-bar { display: flex; align-items: center; gap: 15px; background: #f1f5f9; padding: 12px 20px; border-radius: 30px; margin-top: 20px; }",
	".inv-filter-bar { flex-shrink: 0; display: flex; align-items: center; gap: 15px; background: #f1f5f9; padding: 12px 20px; border-radius: 30px; margin-top: 20px; }",
)

with open(file_path, "w") as f:
	f.write(text)
