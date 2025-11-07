from app.api.v1 import resume

print(f"Resume router has {len(resume.router.routes)} routes")
for route in resume.router.routes:
	print(f"  {route.methods} {route.path}")
