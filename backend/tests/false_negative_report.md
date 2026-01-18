# Fase 39 False Negative Analysis Report

Generated from automated testing of vulnerable code patterns.


## CWE-1321 (Prototype Pollution)


**5 false negative(s) found:**


### Spread operator prototype pollution


**Description:** Using spread operator with user input can copy __proto__


**Expected Rules:** WS003, WS004


**Detected Rules:** None


**Vulnerable Code (spread.js):**

```js
function mergeConfig(userInput) {
    const defaults = { theme: 'dark' };
    return { ...defaults, ...userInput };  // Vulnerable: copies __proto__
}
```


### Lodash merge prototype pollution


**Description:** lodash.merge with user input is a known prototype pollution vector


**Expected Rules:** WS003


**Detected Rules:** None


**Vulnerable Code (lodash.js):**

```js
const _ = require('lodash');

app.post('/settings', (req, res) => {
    const config = {};
    _.merge(config, req.body);  // Vulnerable: CVE-2019-10744
    res.json(config);
});
```


### jQuery extend prototype pollution


**Description:** $.extend with deep copy can pollute prototype


**Expected Rules:** WS003


**Detected Rules:** None


**Vulnerable Code (jquery.js):**

```js
function updateSettings(userSettings) {
    $.extend(true, globalConfig, userSettings);  // Vulnerable when deep=true
}
```


### Reflect.set prototype pollution


**Description:** Reflect.set allows setting __proto__ on objects


**Expected Rules:** WS004


**Detected Rules:** None


**Vulnerable Code (reflect.js):**

```js
function setProperty(obj, key, value) {
    Reflect.set(obj, key, value);  // Vulnerable if key = '__proto__'
}

// Called with user input
setProperty({}, req.body.key, req.body.value);
```


### Object.defineProperty pollution


**Description:** Object.defineProperty can modify prototype chain


**Expected Rules:** WS004


**Detected Rules:** None


**Vulnerable Code (define.js):**

```js
function setProp(obj, prop, val) {
    Object.defineProperty(obj, prop, { value: val, writable: true });
}

// User controls prop name
setProp(target, userInput.propertyName, userInput.value);
```


## CWE-1236 (CSV Injection)


**3 false negative(s) found:**


### String concatenation CSV export


**Description:** Building CSV manually without escaping formulas


**Expected Rules:** WS010, WS011


**Detected Rules:** None


**Vulnerable Code (csv_concat.py):**

```py
def export_csv(users):
    csv_content = "Name,Email\n"
    for user in users:
        csv_content += f"{user.name},{user.email}\n"  # Vulnerable
    return csv_content
```


### CSV response download


**Description:** Sending CSV response without formula sanitization


**Expected Rules:** WS010


**Detected Rules:** None


**Vulnerable Code (download.py):**

```py
from flask import Response

@app.route('/export')
def export_data():
    data = get_user_submitted_data()
    csv_data = generate_csv(data)
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=export.csv'}
    )
```


### DictWriter CSV export


**Description:** Python DictWriter with user data


**Expected Rules:** WS011


**Detected Rules:** WS010


**Vulnerable Code (dictwriter.py):**

```py
import csv

def export_users(users, output_file):
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'email', 'comment'])
        writer.writeheader()
        for user in users:
            writer.writerow(user)  # User 'comment' may start with =@+-
```


## CWE-1284 (Invalid Quantity)


**3 false negative(s) found:**


### Array slice with user input


**Description:** Using slice() with user-controlled bounds


**Expected Rules:** WS020


**Detected Rules:** None


**Vulnerable Code (slice.py):**

```py
def get_page(items, request):
    start = int(request.args.get('start', 0))
    end = int(request.args.get('end', 10))
    return items[start:end]  # No validation on start/end
```


### String multiplication DoS


**Description:** Repeating string by user-controlled count


**Expected Rules:** WS022


**Detected Rules:** None


**Vulnerable Code (string_repeat.js):**

```js
function padString(str, count) {
    const times = parseInt(req.query.repeat);
    return str.repeat(times);  // DoS vector
}
```


### Array constructor size


**Description:** Creating array with user-controlled size


**Expected Rules:** WS022


**Detected Rules:** None


**Vulnerable Code (array_size.js):**

```js
function createGrid(req) {
    const rows = parseInt(req.params.rows);
    const cols = parseInt(req.params.cols);
    return new Array(rows).fill(new Array(cols).fill(0));
}
```


## CWE-427 (Uncontrolled Search Path)


**5 false negative(s) found:**


### exec without absolute path


**Description:** Executing commands by name relies on PATH


**Expected Rules:** PS001, PS002


**Detected Rules:** None


**Vulnerable Code (exec.py):**

```py
import subprocess

def run_tool():
    # Relies on PATH - attacker can place malicious 'mytool' earlier
    subprocess.run(['mytool', '--version'])
```


### child_process exec


**Description:** Node.js exec relies on shell PATH


**Expected Rules:** PS001


**Detected Rules:** None


**Vulnerable Code (child.js):**

```js
const { exec } = require('child_process');

exec('imagemagick convert input.png output.jpg', (err, stdout) => {
    console.log(stdout);  // Relies on PATH
});
```


### PYTHONPATH modification


**Description:** Modifying PYTHONPATH allows module hijacking


**Expected Rules:** PS003


**Detected Rules:** None


**Vulnerable Code (pythonpath.py):**

```py
import os
import sys

# Add user-controlled directory to Python path
user_plugins = os.environ.get('PLUGIN_DIR', '/tmp/plugins')
sys.path.insert(0, user_plugins)  # Vulnerable
```


### require with relative path


**Description:** Node.js require searches node_modules


**Expected Rules:** PS001


**Detected Rules:** None


**Vulnerable Code (require.js):**

```js
// This searches up the directory tree
const plugin = require('user-plugin');  // Could load from cwd/node_modules
```


### LD_LIBRARY_PATH modification


**Description:** Modifying LD_LIBRARY_PATH allows library hijacking


**Expected Rules:** PS002


**Detected Rules:** None


**Vulnerable Code (ldpath.c):**

```c
#include <stdlib.h>

void add_lib_path(const char* path) {
    char* current = getenv("LD_LIBRARY_PATH");
    char* new_path = malloc(strlen(current) + strlen(path) + 2);
    sprintf(new_path, "%s:%s", path, current);
    setenv("LD_LIBRARY_PATH", new_path, 1);  // Vulnerable
}
```


## CWE-428 (Unquoted Search Path)


**4 false negative(s) found:**


### f-string path not quoted


**Description:** Building path with spaces in f-string


**Expected Rules:** PS010


**Detected Rules:** None


**Vulnerable Code (fstring.py):**

```py
import subprocess

def run_app():
    app_path = "C:\\Program Files\\MyApp\\run.exe"
    # Path has spaces but may not be properly quoted when used
    subprocess.Popen(f'{app_path} --config settings.ini', shell=True)
```


### Service binary path


**Description:** Windows service with unquoted binary path


**Expected Rules:** PS011


**Detected Rules:** None


**Vulnerable Code (service.cs):**

```cs
using System.ServiceProcess;

public class MyService : ServiceBase
{
    protected override void OnStart(string[] args)
    {
        // Service executable path with spaces - may be unquoted in registry
        string binaryPath = @"C:\Program Files\MyCompany\Service\svc.exe";
        // When installed, ImagePath might be unquoted
    }
}
```


### Unquoted variable in shell


**Description:** Shell variable with spaces not quoted


**Expected Rules:** PS012


**Detected Rules:** None


**Vulnerable Code (script.sh):**

```sh
#!/bin/bash
APP_DIR="/opt/My Application"
cd $APP_DIR  # Unquoted - breaks on spaces
$APP_DIR/run.sh  # Unquoted execution
```


### Unquoted env var path


**Description:** Environment variable used unquoted in path


**Expected Rules:** PS010, PS012


**Detected Rules:** None


**Vulnerable Code (env_path.py):**

```py
import os
import subprocess

def run_from_env():
    tool_path = os.environ.get('TOOL_PATH', '/default/path')
    # If TOOL_PATH contains spaces, command breaks
    subprocess.call(tool_path + ' --run', shell=True)
```


## CWE-1333 (ReDoS)


**4 false negative(s) found:**


### Email regex backtracking


**Description:** Common email regex with catastrophic backtracking


**Expected Rules:** PS020, PS022


**Detected Rules:** None


**Vulnerable Code (email.py):**

```py
import re

# Common vulnerable email pattern
EMAIL_PATTERN = re.compile(r'^([a-zA-Z0-9_\.-]+)@([\da-zA-Z\.-]+)\.([a-zA-Z\.]{2,6})$')

def validate_email(email):
    return EMAIL_PATTERN.match(email)  # ReDoS on malformed input
```


### HTML tag stripping regex


**Description:** HTML tag regex with backtracking


**Expected Rules:** PS022


**Detected Rules:** None


**Vulnerable Code (strip.py):**

```py
import re

def strip_html(text):
    # Vulnerable to ReDoS on malformed HTML
    return re.sub(r'<[^>]*>', '', text)
```


### Phone number regex


**Description:** Phone validation with alternation


**Expected Rules:** PS020, PS021


**Detected Rules:** None


**Vulnerable Code (phone.java):**

```java
import java.util.regex.Pattern;

public class Validator {
    // Overlapping alternations cause backtracking
    private static final Pattern PHONE = Pattern.compile(
        "^(\\+\\d{1,3}[- ]?)?\\(?\\d{1,4}\\)?[- ]?\\d{1,4}[- ]?\\d{1,4}$"
    );

    public boolean validatePhone(String phone) {
        return PHONE.matcher(phone).matches();
    }
}
```


### Regex from configuration


**Description:** Regex loaded from config (could be user-influenced)


**Expected Rules:** PS023


**Detected Rules:** None


**Vulnerable Code (config_regex.py):**

```py
import re
import yaml

def load_validators():
    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    # Patterns from config - could be DoS patterns
    return {
        name: re.compile(pattern)
        for name, pattern in config['validators'].items()
    }
```


---

## Summary


**Total False Negatives Found:** 24


- CWE-1321 (Prototype Pollution): ❌ 5

- CWE-1236 (CSV Injection): ❌ 3

- CWE-1284 (Invalid Quantity): ❌ 3

- CWE-427 (Uncontrolled Search Path): ❌ 5

- CWE-428 (Unquoted Search Path): ❌ 4

- CWE-1333 (ReDoS): ❌ 4
