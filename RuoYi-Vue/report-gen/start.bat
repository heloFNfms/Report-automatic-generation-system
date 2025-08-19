@echo off
echo Starting Report Generation System...

echo.
echo Building and starting services...
docker-compose up -d --build

echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak > nul

echo.
echo Checking service status...
docker-compose ps

echo.
echo Services are starting up. You can check logs with:
echo   docker-compose logs -f
echo.
echo Access points:
echo   - MCP Server: http://localhost:8000
echo   - Orchestrator: http://localhost:9000
echo   - MySQL: localhost:3306
echo   - Redis: localhost:6379
echo.
echo To stop all services: docker-compose down
echo To stop and remove volumes: docker-compose down -v

pause