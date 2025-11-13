"""API endpoints to generate and fetch test reports."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from ...services.test_report_generator import build_report

router = APIRouter()


@router.get("/generate")
async def generate_report():
	"""Generate a test report from available artifacts and return paths."""
	result = build_report()
	if not result:
		raise HTTPException(status_code=404, detail="No test artifacts found to generate report")
	return JSONResponse(content=result)


@router.get("/html", response_class=HTMLResponse)
async def get_html_report():
	out = Path(__file__).parents[2] / "reports" / "generated" / "api_test_report.html"
	if not out.exists():
		# attempt to build
		build_report()
	if not out.exists():
		raise HTTPException(status_code=404, detail="HTML report not available")
	return HTMLResponse(content=out.read_text(encoding="utf-8"))


@router.get("/download/{fmt}")
async def download_report(fmt: str):
	"""Download the generated report in html/json/csv."""
	base = Path(__file__).parents[2] / "reports" / "generated"
	mapping = {
		"html": base / "api_test_report.html",
		"json": base / "api_test_report.json",
		"csv": base / "api_test_report.csv",
	}
	fmt = fmt.lower()
	if fmt not in mapping:
		raise HTTPException(status_code=400, detail="Unsupported format")
	path = mapping[fmt]
	if not path.exists():
		build_report()
	if not path.exists():
		raise HTTPException(status_code=404, detail="Report file not found")
	return FileResponse(path, filename=path.name)
