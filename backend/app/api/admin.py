from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi_nextauth_jwt import NextAuthJWT
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from dependency_injector.wiring import Provide, inject
from typing import Annotated
import os
import asyncio
from pathlib import Path
from datetime import timedelta

from app.core.container import Container
from app.core.database import get_db
from app.services.excel_import_service import ExcelImportService
from app.services.restaurant_import_service import RestaurantImportService
from app.services.file_storage_service import S3FileStorageService
from app.services.canned_audio_service import CannedAudioService
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])

# Initialize NextAuth JWT
JWT = NextAuthJWT(
    secret=os.getenv("JWT_SECRET", "your-jwt-secret-key-here")
)

@router.get("/login")
async def admin_login_page():
    """Serve the admin login page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI DriveThru Admin</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 400px;
            }
            .header {
                text-align: center;
                margin-bottom: 2rem;
            }
            .header h1 {
                color: #333;
                margin: 0;
                font-size: 1.8rem;
            }
            .header p {
                color: #666;
                margin: 0.5rem 0 0 0;
            }
            .form-group {
                margin-bottom: 1rem;
            }
            label {
                display: block;
                margin-bottom: 0.5rem;
                color: #333;
                font-weight: 500;
            }
            input[type="text"], input[type="password"] {
                width: 100%;
                padding: 0.75rem;
                border: 2px solid #e1e5e9;
                border-radius: 5px;
                font-size: 1rem;
                transition: border-color 0.3s;
                box-sizing: border-box;
            }
            input[type="text"]:focus, input[type="password"]:focus {
                outline: none;
                border-color: #667eea;
            }
            .btn {
                width: 100%;
                padding: 0.75rem;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #5a6fd8;
            }
            .error {
                color: #e74c3c;
                margin-top: 1rem;
                text-align: center;
            }
            .success {
                color: #27ae60;
                margin-top: 1rem;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>AI DriveThru Admin</h1>
                <p>Restaurant Data Management</p>
            </div>
            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="btn">Login</button>
            </form>
            <div id="message"></div>
        </div>

        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const messageDiv = document.getElementById('message');
                
                try {
                    const response = await fetch('/admin/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ username, password })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        messageDiv.innerHTML = '<div class="success">Login successful! Redirecting...</div>';
                        // Store token and redirect to admin dashboard
                        localStorage.setItem('admin_token', data.access_token);
                        setTimeout(() => {
                            window.location.href = '/admin/dashboard';
                        }, 1000);
                    } else {
                        messageDiv.innerHTML = `<div class="error">${data.detail}</div>`;
                    }
                } catch (error) {
                    messageDiv.innerHTML = '<div class="error">Login failed. Please try again.</div>';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.post("/login")
async def admin_login(credentials: dict):
    """Admin login endpoint"""
    username = credentials.get("username")
    password = credentials.get("password")
    
    # Simple hardcoded credentials (in production, use proper user management)
    if username == os.getenv("ADMIN_USERNAME", "admin") and password == os.getenv("ADMIN_PASSWORD", "admin123"):
        # Generate JWT token
        token = JWT.create_access_token(
            subject=username,
            expires_delta=timedelta(hours=1)
        )
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@router.get("/dashboard")
async def admin_dashboard(jwt: Annotated[dict, Depends(JWT)]):
    """Admin dashboard page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI DriveThru Admin Dashboard</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f7fa;
                margin: 0;
                padding: 0;
                min-height: 100vh;
            }
            .header {
                background: white;
                padding: 1rem 2rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .header h1 {
                color: #333;
                margin: 0;
            }
            .logout-btn {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 5px;
                cursor: pointer;
            }
            .container {
                max-width: 1200px;
                margin: 2rem auto;
                padding: 0 2rem;
            }
            .upload-section {
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
            .upload-section h2 {
                color: #333;
                margin-top: 0;
            }
            .form-group {
                margin-bottom: 1rem;
            }
            label {
                display: block;
                margin-bottom: 0.5rem;
                color: #333;
                font-weight: 500;
            }
            input[type="file"] {
                width: 100%;
                padding: 0.75rem;
                border: 2px dashed #ddd;
                border-radius: 5px;
                cursor: pointer;
            }
            .btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1rem;
                margin-right: 1rem;
            }
            .btn:hover {
                background: #5a6fd8;
            }
            .btn-secondary {
                background: #6c757d;
            }
            .btn-secondary:hover {
                background: #5a6268;
            }
            .status {
                margin-top: 1rem;
                padding: 1rem;
                border-radius: 5px;
                display: none;
            }
            .status.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .status.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .status.info {
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>AI DriveThru Admin Dashboard</h1>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
        
        <div class="container">
            <div class="upload-section">
                <h2>Import Restaurant Data</h2>
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="excelFile">Excel File (.xlsx)</label>
                        <input type="file" id="excelFile" name="excel_file" accept=".xlsx" required>
                    </div>
                    <div class="form-group">
                        <label for="imagesFolder">Images Folder (optional)</label>
                        <input type="file" id="imagesFolder" name="images_folder" webkitdirectory directory multiple>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="overwrite" name="overwrite"> Overwrite existing records
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="generateAudio" name="generate_audio" checked> Generate audio files
                        </label>
                    </div>
                    <button type="submit" class="btn">Import Data</button>
                    <button type="button" class="btn btn-secondary" onclick="checkStatus()">Check Status</button>
                </form>
                <div id="status" class="status"></div>
            </div>
        </div>

        <script>
            const token = localStorage.getItem('admin_token');
            if (!token) {
                window.location.href = '/admin/login';
            }

            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData();
                const excelFile = document.getElementById('excelFile').files[0];
                const imagesFolder = document.getElementById('imagesFolder').files;
                const overwrite = document.getElementById('overwrite').checked;
                const generateAudio = document.getElementById('generateAudio').checked;
                
                if (!excelFile) {
                    showStatus('Please select an Excel file', 'error');
                    return;
                }
                
                formData.append('excel_file', excelFile);
                
                // Add images if selected
                for (let file of imagesFolder) {
                    formData.append('images', file);
                }
                
                formData.append('overwrite', overwrite);
                formData.append('generate_audio', generateAudio);
                
                showStatus('Uploading and processing...', 'info');
                
                try {
                    const response = await fetch('/admin/import', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        },
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        showStatus('Import completed successfully!', 'success');
                    } else {
                        showStatus(`Import failed: ${data.detail}`, 'error');
                    }
                } catch (error) {
                    showStatus('Upload failed. Please try again.', 'error');
                }
            });

            function showStatus(message, type) {
                const statusDiv = document.getElementById('status');
                statusDiv.textContent = message;
                statusDiv.className = `status ${type}`;
                statusDiv.style.display = 'block';
            }

            function logout() {
                localStorage.removeItem('admin_token');
                window.location.href = '/admin/login';
            }

            function checkStatus() {
                showStatus('Checking system status...', 'info');
                // Add status check logic here
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.post("/import")
@inject
async def admin_import(
    excel_file: UploadFile = File(...),
    images: list[UploadFile] = File(None),
    overwrite: bool = Form(False),
    generate_audio: bool = Form(True),
    jwt: Annotated[dict, Depends(JWT)] = None,
    excel_import_service: ExcelImportService = Depends(Provide[Container.excel_import_service]),
    restaurant_import_service: RestaurantImportService = Depends(Provide[Container.restaurant_import_service]),
    file_storage_service: S3FileStorageService = Depends(Provide[Container.file_storage_service]),
    audio_generation_service: CannedAudioService = Depends(Provide[Container.canned_audio_service]),
    db: AsyncSession = Depends(get_db)
):
    """Admin import endpoint - protected with JWT"""
    try:
        # Read Excel file
        excel_data = await excel_file.read()
        
        # Parse and validate Excel
        parse_result = await excel_import_service.parse_restaurant_excel(excel_data)
        if not parse_result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Excel parsing failed: {parse_result.error_message}"
            )
        
        # Import restaurant data
        import_result = await restaurant_import_service.import_restaurant_data(
            restaurant_data=parse_result.data,
            excel_file=excel_data,
            images_folder=images if images else None,
            overwrite_existing=overwrite,
            import_menu=True,
            upload_images=True,
            generate_audio=generate_audio
        )
        
        if import_result.success:
            return {
                "message": "Import completed successfully",
                "restaurant_id": import_result.data.get("restaurant_id"),
                "items_imported": import_result.data.get("items_imported", 0)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Import failed: {import_result.error_message}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )
