html = """
<!DOCTYPE html>
<html>
    <head>
    <style>
    table {{
      font-family: arial, sans-serif;
      border-collapse: collapse;
      width: 100%;
    }}
    
    td, th {{
      border: 1px solid #000000;
      text-align: left;
      padding: 8px;
    }}
    
    tr:nth-child(even) {{
      background-color: #dddddd;
    }}
    </style>
    </head>
    <body>
        <table>
            <tr>
              <th>Module</th>
              <th>Version</th>
              <th>Release Date</th>
              <th>Details</th>
            </tr>
            {content}
        </table>
    </body>
</html>
"""
