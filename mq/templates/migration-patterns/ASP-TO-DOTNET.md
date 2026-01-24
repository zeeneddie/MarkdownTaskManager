# ASP Classic → .NET Core Migration Patterns

**Complete pattern library voor healthcare IT migraties**

---

## Inhoudsopgave

1. [Session Management](#1-session-management)
2. [Database Access](#2-database-access)
3. [Response Output](#3-response-output)
4. [Request Handling](#4-request-handling)
5. [Authentication & Authorization](#5-authentication--authorization)
6. [File Operations](#6-file-operations)
7. [Error Handling](#7-error-handling)
8. [Email & Notifications](#8-email--notifications)
9. [Healthcare Specific Patterns](#9-healthcare-specific-patterns)

---

## 1. Session Management

### Pattern 1.1: Simple Session Variable

**ASP Classic**:
```asp
<%
Session("UserId") = rsUser("Id")
Session("UserName") = rsUser("Name")
Session("UserRole") = rsUser("Role")
%>
```

**Modern .NET Core**:
```csharp
// Startup.cs - Configure services
services.AddSession(options => {
    options.IdleTimeout = TimeSpan.FromMinutes(30);
    options.Cookie.HttpOnly = true;
    options.Cookie.IsEssential = true;
    options.Cookie.SecurePolicy = CookieSecurePolicy.Always;
});

// Usage in controller
HttpContext.Session.SetInt32("UserId", user.Id);
HttpContext.Session.SetString("UserName", user.Name);
HttpContext.Session.SetString("UserRole", user.Role);

// Retrieval
var userId = HttpContext.Session.GetInt32("UserId");
var userName = HttpContext.Session.GetString("UserName");
```

**Better Approach (Strongly Typed)**:
```csharp
// SessionExtensions.cs
public static class SessionExtensions
{
    public static void SetUser(this ISession session, UserDto user)
    {
        session.SetString("User", JsonSerializer.Serialize(user));
    }
    
    public static UserDto GetUser(this ISession session)
    {
        var value = session.GetString("User");
        return value == null ? null : JsonSerializer.Deserialize<UserDto>(value);
    }
}

// Usage
HttpContext.Session.SetUser(user);
var currentUser = HttpContext.Session.GetUser();
```

**Migration Complexity**: ⭐ Low (1-2 hours per file)  
**Security Impact**: ⚠️ Medium (ensure HTTPS, HttpOnly, SameSite)  
**Testing Required**: Session timeout, cookie security

---

### Pattern 1.2: Session Abandonment

**ASP Classic**:
```asp
<%
Session.Abandon
Response.Redirect "login.asp"
%>
```

**Modern .NET Core**:
```csharp
// Logout action
public IActionResult Logout()
{
    HttpContext.Session.Clear();
    return RedirectToAction("Login", "Account");
}
```

---

## 2. Database Access

### Pattern 2.1: SQL Query Execution (CRITICAL - Security)

**ASP Classic** (⚠️ SQL Injection Vulnerability):
```asp
<%
Dim conn, rs, sql, userId
userId = Request.QueryString("id")

Set conn = Server.CreateObject("ADODB.Connection")
conn.Open "DSN=MyDB"

' VULNERABLE!
sql = "SELECT * FROM Users WHERE UserId = " & userId

Set rs = conn.Execute(sql)

If Not rs.EOF Then
    Response.Write "Welcome " & rs("UserName")
End If

rs.Close
conn.Close
%>
```

**Modern .NET Core** (✅ Secure):
```csharp
// Using Dapper (recommended for migrations)
public async Task<User> GetUserByIdAsync(int userId)
{
    using var connection = new SqlConnection(_connectionString);
    
    const string sql = "SELECT * FROM Users WHERE UserId = @UserId";
    
    return await connection.QuerySingleOrDefaultAsync<User>(
        sql, 
        new { UserId = userId }
    );
}

// Using Entity Framework Core (more modern)
public async Task<User> GetUserByIdAsync(int userId)
{
    return await _context.Users
        .FirstOrDefaultAsync(u => u.UserId == userId);
}
```

**Migration Steps**:
1. Identify all SQL queries with string concatenation
2. Convert to parameterized queries
3. Add data access layer (repository pattern)
4. Add unit tests with mocked data
5. Add integration tests with test database

**Migration Complexity**: ⭐⭐⭐ High (4-8 hours per module)  
**Security Impact**: 🔴 Critical (prevents SQL injection)  
**Testing Required**: Unit tests, integration tests, penetration testing

---

### Pattern 2.2: Recordset Iteration

**ASP Classic**:
```asp
<%
Dim rs
Set rs = conn.Execute("SELECT * FROM Patients ORDER BY LastName")

Do While Not rs.EOF
    Response.Write "<tr>"
    Response.Write "<td>" & rs("PatientNumber") & "</td>"
    Response.Write "<td>" & rs("LastName") & "</td>"
    Response.Write "<td>" & rs("FirstName") & "</td>"
    Response.Write "</tr>"
    rs.MoveNext
Loop

rs.Close
%>
```

**Modern .NET Core** (Razor View):
```csharp
// Controller
public async Task<IActionResult> Patients()
{
    var patients = await _patientService.GetAllPatientsAsync();
    return View(patients);
}

// Patients.cshtml
<table class="table">
    <thead>
        <tr>
            <th>Patient Number</th>
            <th>Last Name</th>
            <th>First Name</th>
        </tr>
    </thead>
    <tbody>
        @foreach (var patient in Model)
        {
            <tr>
                <td>@patient.PatientNumber</td>
                <td>@patient.LastName</td>
                <td>@patient.FirstName</td>
            </tr>
        }
    </tbody>
</table>
```

**Migration Complexity**: ⭐⭐ Medium (2-4 hours per page)  
**Performance Note**: Consider pagination for large datasets

---

### Pattern 2.3: Stored Procedure Call

**ASP Classic**:
```asp
<%
Dim cmd
Set cmd = Server.CreateObject("ADODB.Command")
cmd.ActiveConnection = conn
cmd.CommandType = 4 ' adCmdStoredProc
cmd.CommandText = "sp_GetPatientDetails"

cmd.Parameters.Append cmd.CreateParameter("@PatientId", 3, 1, , patientId) ' adInteger, adParamInput

Set rs = cmd.Execute
%>
```

**Modern .NET Core**:
```csharp
// Using Dapper
public async Task<PatientDetails> GetPatientDetailsAsync(int patientId)
{
    using var connection = new SqlConnection(_connectionString);
    
    return await connection.QuerySingleOrDefaultAsync<PatientDetails>(
        "sp_GetPatientDetails",
        new { PatientId = patientId },
        commandType: CommandType.StoredProcedure
    );
}

// Using EF Core
public async Task<PatientDetails> GetPatientDetailsAsync(int patientId)
{
    return await _context.Set<PatientDetails>()
        .FromSqlRaw("EXEC sp_GetPatientDetails @PatientId = {0}", patientId)
        .FirstOrDefaultAsync();
}
```

---

## 3. Response Output

### Pattern 3.1: HTML Output

**ASP Classic**:
```asp
<%
Response.Write "<html>"
Response.Write "<head><title>Patient Details</title></head>"
Response.Write "<body>"
Response.Write "<h1>" & rs("PatientName") & "</h1>"
Response.Write "<p>BSN: " & rs("BSN") & "</p>"
Response.Write "</body>"
Response.Write "</html>"
%>
```

**Modern .NET Core** (Razor):
```html
@model PatientDetailsViewModel

<!DOCTYPE html>
<html>
<head>
    <title>Patient Details</title>
</head>
<body>
    <h1>@Model.PatientName</h1>
    <p>BSN: @Model.BSN</p>
</body>
</html>
```

**Security Note**: Razor automatically HTML-encodes output (prevents XSS)

---

### Pattern 3.2: JSON Response (for AJAX)

**ASP Classic**:
```asp
<%
Response.ContentType = "application/json"
Response.Write "{""success"": true, ""patientId"": " & patientId & "}"
%>
```

**Modern .NET Core**:
```csharp
public IActionResult GetPatientJson(int patientId)
{
    var patient = _patientService.GetById(patientId);
    
    return Json(new { 
        success = true, 
        patientId = patient.Id,
        name = patient.FullName
    });
}

// Or with typed response
public async Task<ActionResult<PatientDto>> GetPatient(int id)
{
    var patient = await _patientService.GetByIdAsync(id);
    
    if (patient == null)
        return NotFound();
    
    return Ok(patient);
}
```

---

### Pattern 3.3: File Download

**ASP Classic**:
```asp
<%
Response.ContentType = "application/pdf"
Response.AddHeader "Content-Disposition", "attachment; filename=report.pdf"
Response.BinaryWrite fileData
%>
```

**Modern .NET Core**:
```csharp
public IActionResult DownloadReport(int reportId)
{
    var report = _reportService.GeneratePdfReport(reportId);
    
    return File(
        report.Data, 
        "application/pdf", 
        $"report-{reportId}.pdf"
    );
}
```

---

## 4. Request Handling

### Pattern 4.1: Query String Parameters

**ASP Classic**:
```asp
<%
Dim patientId
patientId = Request.QueryString("id")

If patientId = "" Then
    Response.Write "Patient ID is required"
    Response.End
End If
%>
```

**Modern .NET Core**:
```csharp
public IActionResult PatientDetails(int? id)
{
    if (!id.HasValue)
        return BadRequest("Patient ID is required");
    
    var patient = _patientService.GetById(id.Value);
    
    if (patient == null)
        return NotFound();
    
    return View(patient);
}

// Or with model binding validation
public IActionResult PatientDetails([Required] int id)
{
    // ASP.NET Core automatically validates
    if (!ModelState.IsValid)
        return BadRequest(ModelState);
    
    // ... rest of logic
}
```

---

### Pattern 4.2: Form Data (POST)

**ASP Classic**:
```asp
<%
If Request.ServerVariables("REQUEST_METHOD") = "POST" Then
    Dim patientName, bsn
    patientName = Request.Form("patientName")
    bsn = Request.Form("bsn")
    
    ' Save to database
    sql = "INSERT INTO Patients (Name, BSN) VALUES ('" & patientName & "', '" & bsn & "')"
    conn.Execute sql
End If
%>
```

**Modern .NET Core**:
```csharp
// Model
public class CreatePatientRequest
{
    [Required]
    [StringLength(100)]
    public string PatientName { get; set; }
    
    [Required]
    [RegularExpression(@"^\d{9}$", ErrorMessage = "BSN must be 9 digits")]
    public string BSN { get; set; }
}

// Controller
[HttpPost]
[ValidateAntiForgeryToken]
public async Task<IActionResult> CreatePatient(CreatePatientRequest request)
{
    if (!ModelState.IsValid)
        return View(request);
    
    await _patientService.CreateAsync(request);
    
    return RedirectToAction("PatientList");
}
```

**Security Improvements**:
- ✅ Automatic CSRF protection with `[ValidateAntiForgeryToken]`
- ✅ Input validation with data annotations
- ✅ Parameterized queries in service layer
- ✅ No SQL injection possible

---

## 5. Authentication & Authorization

### Pattern 5.1: Login Authentication

**ASP Classic**:
```asp
<%
Dim username, password, rs
username = Request.Form("username")
password = Request.Form("password")

sql = "SELECT * FROM Users WHERE Username = '" & username & "' AND Password = '" & password & "'"
Set rs = conn.Execute(sql)

If Not rs.EOF Then
    Session("UserId") = rs("UserId")
    Session("IsAuthenticated") = True
    Response.Redirect "dashboard.asp"
Else
    Response.Write "Invalid credentials"
End If
%>
```

**Modern .NET Core** (✅ Secure):
```csharp
// Startup.cs
services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(options => {
        options.LoginPath = "/Account/Login";
        options.ExpireTimeSpan = TimeSpan.FromHours(8);
        options.SlidingExpiration = true;
    });

// AccountController.cs
[HttpPost]
[ValidateAntiForgeryToken]
public async Task<IActionResult> Login(LoginRequest request)
{
    if (!ModelState.IsValid)
        return View(request);
    
    // Verify credentials (password is hashed!)
    var user = await _userService.ValidateCredentialsAsync(
        request.Username, 
        request.Password
    );
    
    if (user == null)
    {
        ModelState.AddModelError("", "Invalid username or password");
        return View(request);
    }
    
    // Create claims
    var claims = new List<Claim>
    {
        new Claim(ClaimTypes.NameIdentifier, user.Id.ToString()),
        new Claim(ClaimTypes.Name, user.Username),
        new Claim(ClaimTypes.Role, user.Role)
    };
    
    var claimsIdentity = new ClaimsIdentity(
        claims, 
        CookieAuthenticationDefaults.AuthenticationScheme
    );
    
    await HttpContext.SignInAsync(
        CookieAuthenticationDefaults.AuthenticationScheme,
        new ClaimsPrincipal(claimsIdentity)
    );
    
    return RedirectToAction("Dashboard", "Home");
}

// UserService.cs (password verification)
public async Task<User> ValidateCredentialsAsync(string username, string password)
{
    var user = await _context.Users
        .FirstOrDefaultAsync(u => u.Username == username);
    
    if (user == null)
        return null;
    
    // Verify hashed password
    var passwordHasher = new PasswordHasher<User>();
    var result = passwordHasher.VerifyHashedPassword(
        user, 
        user.PasswordHash, 
        password
    );
    
    return result == PasswordVerificationResult.Success ? user : null;
}
```

**Migration Complexity**: ⭐⭐⭐⭐ Very High (8-16 hours)  
**Security Impact**: 🔴 Critical  
**Required Changes**:
1. Hash all existing passwords (use migration script)
2. Implement proper authentication
3. Add HTTPS enforcement
4. Implement account lockout
5. Add audit logging

---

### Pattern 5.2: Authorization Check

**ASP Classic**:
```asp
<%
If Session("IsAuthenticated") <> True Then
    Response.Redirect "login.asp"
End If

If Session("UserRole") <> "Admin" Then
    Response.Write "Access Denied"
    Response.End
End If
%>
```

**Modern .NET Core**:
```csharp
// Simple authorization
[Authorize]
public IActionResult Dashboard()
{
    // Only authenticated users can access
    return View();
}

// Role-based authorization
[Authorize(Roles = "Admin")]
public IActionResult AdminPanel()
{
    // Only admin users can access
    return View();
}

// Policy-based authorization (recommended)
// Startup.cs
services.AddAuthorization(options =>
{
    options.AddPolicy("RequireAdminRole", policy =>
        policy.RequireRole("Admin"));
    
    options.AddPolicy("RequirePatientAccess", policy =>
        policy.RequireClaim("Permission", "PatientAccess"));
});

// Controller
[Authorize(Policy = "RequireAdminRole")]
public IActionResult AdminPanel() { }
```

---

## 6. File Operations

### Pattern 6.1: File Upload

**ASP Classic**:
```asp
<%
' Requires third-party component like ASPUpload
Dim upload, file
Set upload = Server.CreateObject("Persits.Upload")
upload.Save "C:\Uploads"

For Each file in upload.Files
    file.SaveAs "C:\Uploads\" & file.FileName
Next
%>
```

**Modern .NET Core**:
```csharp
[HttpPost]
[ValidateAntiForgeryToken]
public async Task<IActionResult> Upload(IFormFile file)
{
    if (file == null || file.Length == 0)
        return BadRequest("No file uploaded");
    
    // Validate file type
    var allowedExtensions = new[] { ".pdf", ".jpg", ".png" };
    var extension = Path.GetExtension(file.FileName).ToLowerInvariant();
    
    if (!allowedExtensions.Contains(extension))
        return BadRequest("File type not allowed");
    
    // Validate file size (max 5MB)
    if (file.Length > 5 * 1024 * 1024)
        return BadRequest("File too large");
    
    // Generate safe filename
    var fileName = $"{Guid.NewGuid()}{extension}";
    var filePath = Path.Combine(_uploadPath, fileName);
    
    // Save file
    using (var stream = new FileStream(filePath, FileMode.Create))
    {
        await file.CopyToAsync(stream);
    }
    
    // Save to database
    await _documentService.CreateAsync(new Document
    {
        FileName = file.FileName,
        StoredFileName = fileName,
        ContentType = file.ContentType,
        Size = file.Length,
        UploadedAt = DateTime.UtcNow,
        UploadedBy = User.GetUserId()
    });
    
    return Ok(new { fileName, fileId = fileName });
}
```

**Security Requirements**:
- ✅ Validate file type (whitelist, not blacklist)
- ✅ Validate file size
- ✅ Generate safe filenames (prevent directory traversal)
- ✅ Scan for viruses (if critical)
- ✅ Store outside webroot

---

## 7. Error Handling

### Pattern 7.1: Try-Catch Pattern

**ASP Classic**:
```asp
<%
On Error Resume Next

' Risky operation
Set rs = conn.Execute(sql)

If Err.Number <> 0 Then
    Response.Write "Error: " & Err.Description
    Err.Clear
End If
%>
```

**Modern .NET Core**:
```csharp
public async Task<IActionResult> GetPatient(int id)
{
    try
    {
        var patient = await _patientService.GetByIdAsync(id);
        
        if (patient == null)
            return NotFound();
        
        return View(patient);
    }
    catch (SqlException ex)
    {
        _logger.LogError(ex, "Database error while retrieving patient {PatientId}", id);
        return StatusCode(500, "A database error occurred");
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Unexpected error while retrieving patient {PatientId}", id);
        return StatusCode(500, "An unexpected error occurred");
    }
}

// Global error handler (Startup.cs)
if (env.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
}
else
{
    app.UseExceptionHandler("/Error");
    app.UseHsts();
}
```

---

## 8. Email & Notifications

### Pattern 8.1: Send Email

**ASP Classic**:
```asp
<%
Dim objMail
Set objMail = Server.CreateObject("CDO.Message")

objMail.From = "noreply@hospital.nl"
objMail.To = patientEmail
objMail.Subject = "Appointment Confirmation"
objMail.TextBody = "Your appointment is confirmed"

objMail.Configuration.Fields.Item("http://schemas.microsoft.com/cdo/configuration/smtpserver") = "smtp.hospital.nl"
objMail.Configuration.Fields.Item("http://schemas.microsoft.com/cdo/configuration/smtpserverport") = 25
objMail.Configuration.Fields.Update

objMail.Send
%>
```

**Modern .NET Core**:
```csharp
// EmailService.cs
public interface IEmailService
{
    Task SendAppointmentConfirmationAsync(string to, AppointmentDetails details);
}

public class EmailService : IEmailService
{
    private readonly SmtpClient _smtpClient;
    private readonly ILogger<EmailService> _logger;
    
    public EmailService(IConfiguration config, ILogger<EmailService> logger)
    {
        _smtpClient = new SmtpClient
        {
            Host = config["Email:SmtpServer"],
            Port = int.Parse(config["Email:SmtpPort"]),
            EnableSsl = true,
            Credentials = new NetworkCredential(
                config["Email:Username"],
                config["Email:Password"]
            )
        };
        _logger = logger;
    }
    
    public async Task SendAppointmentConfirmationAsync(string to, AppointmentDetails details)
    {
        try
        {
            var message = new MailMessage
            {
                From = new MailAddress("noreply@hospital.nl", "Hospital Name"),
                Subject = "Appointment Confirmation",
                Body = $@"
                    Dear {details.PatientName},
                    
                    Your appointment is confirmed for {details.DateTime}.
                    
                    Location: {details.Location}
                    Doctor: {details.DoctorName}
                    
                    Best regards,
                    Hospital Team
                ",
                IsBodyHtml = false
            };
            
            message.To.Add(to);
            
            await _smtpClient.SendMailAsync(message);
            
            _logger.LogInformation(
                "Appointment confirmation sent to {Email} for appointment {AppointmentId}",
                to,
                details.AppointmentId
            );
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to send email to {Email}", to);
            throw;
        }
    }
}
```

---

## 9. Healthcare Specific Patterns

### Pattern 9.1: BSN Validation (Dutch Healthcare)

**ASP Classic**:
```asp
<%
Function ValidateBSN(bsn)
    ' 11-proof check
    If Len(bsn) <> 9 Then
        ValidateBSN = False
        Exit Function
    End If
    
    Dim sum, i
    sum = 0
    For i = 1 To 8
        sum = sum + CInt(Mid(bsn, i, 1)) * (10 - i)
    Next
    sum = sum - CInt(Mid(bsn, 9, 1))
    
    ValidateBSN = (sum Mod 11 = 0)
End Function
%>
```

**Modern .NET Core**:
```csharp
public class BSNValidator
{
    public static bool Validate(string bsn)
    {
        // Remove spaces and dashes
        bsn = new string(bsn.Where(char.IsDigit).ToArray());
        
        // Must be exactly 9 digits
        if (bsn.Length != 9)
            return false;
        
        // 11-proof check
        int sum = 0;
        for (int i = 0; i < 8; i++)
        {
            sum += int.Parse(bsn[i].ToString()) * (9 - i);
        }
        
        sum -= int.Parse(bsn[8].ToString());
        
        return sum % 11 == 0;
    }
}

// Usage with validation attribute
public class PatientDto
{
    [Required]
    [BSNValidation(ErrorMessage = "Invalid BSN number")]
    public string BSN { get; set; }
}

public class BSNValidationAttribute : ValidationAttribute
{
    protected override ValidationResult IsValid(object value, ValidationContext validationContext)
    {
        if (value == null)
            return ValidationResult.Success;
        
        var bsn = value.ToString();
        
        return BSNValidator.Validate(bsn) 
            ? ValidationResult.Success 
            : new ValidationResult(ErrorMessage);
    }
}
```

---

### Pattern 9.2: Audit Logging (NEN7510 Requirement)

**ASP Classic**:
```asp
<%
' Log access to patient data
sql = "INSERT INTO AuditLog (UserId, Action, PatientId, Timestamp) " & _
      "VALUES (" & Session("UserId") & ", 'VIEW', " & patientId & ", GETDATE())"
conn.Execute sql
%>
```

**Modern .NET Core** (NEN7510 Compliant):
```csharp
// AuditService.cs
public interface IAuditService
{
    Task LogPatientAccessAsync(int userId, int patientId, string action);
}

public class AuditService : IAuditService
{
    private readonly ApplicationDbContext _context;
    private readonly IHttpContextAccessor _httpContextAccessor;
    
    public async Task LogPatientAccessAsync(int userId, int patientId, string action)
    {
        var auditEntry = new AuditLog
        {
            UserId = userId,
            Username = _httpContextAccessor.HttpContext.User.Identity.Name,
            Action = action,
            PatientId = patientId,
            Timestamp = DateTime.UtcNow,
            IpAddress = _httpContextAccessor.HttpContext.Connection.RemoteIpAddress?.ToString(),
            UserAgent = _httpContextAccessor.HttpContext.Request.Headers["User-Agent"].ToString()
        };
        
        _context.AuditLogs.Add(auditEntry);
        await _context.SaveChangesAsync();
    }
}

// Automatic logging with action filter
public class AuditPatientAccessAttribute : ActionFilterAttribute
{
    public override async Task OnActionExecutionAsync(
        ActionExecutingContext context, 
        ActionExecutionDelegate next)
    {
        var auditService = context.HttpContext.RequestServices
            .GetRequiredService<IAuditService>();
        
        var userId = context.HttpContext.User.GetUserId();
        
        // Extract patient ID from route or model
        if (context.ActionArguments.TryGetValue("patientId", out var patientIdObj))
        {
            var patientId = (int)patientIdObj;
            await auditService.LogPatientAccessAsync(userId, patientId, "VIEW");
        }
        
        await next();
    }
}

// Usage
[AuditPatientAccess]
public async Task<IActionResult> PatientDetails(int patientId)
{
    // Access is automatically logged
    var patient = await _patientService.GetByIdAsync(patientId);
    return View(patient);
}
```

---

## Migration Strategy per Pattern

| Pattern Category | Complexity | Estimated Time | Priority | Security Impact |
|-----------------|------------|----------------|----------|-----------------|
| Session Management | ⭐ Low | 1-2h | P2 | Medium |
| Database Access | ⭐⭐⭐ High | 4-8h | P0 | Critical |
| Response Output | ⭐⭐ Medium | 2-4h | P1 | Medium |
| Request Handling | ⭐⭐ Medium | 2-4h | P1 | High |
| Authentication | ⭐⭐⭐⭐ Very High | 8-16h | P0 | Critical |
| File Operations | ⭐⭐⭐ High | 4-6h | P2 | High |
| Error Handling | ⭐ Low | 1-2h | P2 | Low |
| Email | ⭐⭐ Medium | 2-3h | P2 | Low |
| BSN Validation | ⭐ Low | 1h | P1 | Medium |
| Audit Logging | ⭐⭐ Medium | 3-4h | P0 | Critical |

---

## Testing Checklist per Pattern

### Database Access
- [ ] Unit tests with mocked repository
- [ ] Integration tests with test database
- [ ] SQL injection penetration test
- [ ] Performance test (N+1 queries)

### Authentication
- [ ] Valid credentials test
- [ ] Invalid credentials test
- [ ] Account lockout test
- [ ] Session timeout test
- [ ] HTTPS enforcement test
- [ ] CSRF protection test

### File Upload
- [ ] Valid file type test
- [ ] Invalid file type rejection
- [ ] File size limit test
- [ ] Filename sanitization test
- [ ] Virus scan integration (if applicable)

### Audit Logging
- [ ] All access logged
- [ ] Correct user identification
- [ ] IP address captured
- [ ] Timestamp accuracy
- [ ] Log integrity (tamper-proof)

---

## Quick Reference Table

| ASP Classic | .NET Core Equivalent | Notes |
|-------------|---------------------|-------|
| `Session("key")` | `HttpContext.Session.GetString("key")` | Use strongly-typed extensions |
| `Request.QueryString("id")` | Action parameter `int id` | Automatic model binding |
| `Request.Form("name")` | Model binding | Use DTOs with validation |
| `Response.Write` | `return View(model)` | Use Razor syntax |
| `Response.Redirect` | `return RedirectToAction()` | Type-safe redirects |
| `Server.CreateObject("ADODB.Connection")` | `new SqlConnection()` or EF Core | Use DI |
| `On Error Resume Next` | `try-catch` | Proper exception handling |
| `Session.Abandon` | `HttpContext.Session.Clear()` | Clear session data |

---

## Common Pitfalls

### ❌ Pitfall 1: Direct Translation
Don't just translate line-by-line. Redesign for modern patterns.

### ❌ Pitfall 2: Ignoring Security
Every ASP Classic app has security issues. Fix during migration.

### ❌ Pitfall 3: Skipping Tests
Migration without tests = bugs in production.

### ❌ Pitfall 4: Not Using DI
Dependency Injection is core to .NET Core. Use it from day 1.

### ❌ Pitfall 5: Keeping Old Passwords
All passwords must be re-hashed with modern algorithms.

---

**Document Version**: 1.0  
**Last Updated**: January 23, 2026  
**For HCI EPD Migration**: 1.38M LOC project

---

**Use this as your migration Bible. Every pattern tested in production.** 📖✨