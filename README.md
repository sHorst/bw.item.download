Download Item
-------------

This is a download and verify plugin for Bundlewrap. It will download a given url to the Host and verifies that the file has the correct hash.

Demo Metadata
-------------

```python
downloads = {
    '/opt/bin/myProgram': {
        'url': 'https://myServer.net/myProgram',
        'sha256': '78abad9b589f303f6d9c129ed5ebfe240fbdbdaa5bb0ffec43dacb2991bd526a',
        'owner': 'root',
        'group': 'root',
        'mode': '0644',
    }
}
```
