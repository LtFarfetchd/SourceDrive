FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'

# https://developers.google.com/drive/api/v3/ref-export-formats
DRIVE_EXPORT_MIMETYPES = {
    'application/vnd.google-apps.document': {
        'name': 'doc', 
        'exports': {
            'application/rtf': 'rtf',
            'application/vnd.oasis.opendocument.text': 'odt',
            'text/html': 'html',
            'application/pdf': 'pdf',
            'application/epub+zip': 'epub',
            'application/zip': 'zip',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'text/plain': 'txt'
        },
        'default_export': 'application/rtf'
    },
    'application/vnd.google-apps.spreadsheet': {
        'name': 'sheet', 
        'exports': {
            'application/x-vnd.oasis.opendocument.spreadsheet': 'ods',
            'text/tab-separated-values': 'tsv',
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'text/csv': 'csv',
            'application/zip': 'zip',
            'application/vnd.oasis.opendocument.spreadsheet': 'ods'
        },
        'default_export': 'text/tab-separated-values'
    },
    'application/vnd.google-apps.drawing': {
        'name': 'drawing', 
        'exports': {
            'image/svg+xml': 'svg',
            'image/png': 'png',
            'application/pdf': 'pdf',
            'image/jpeg': 'jpeg'
        },
        'default_export': 'image/png'
    },
    'application/vnd.google-apps.presentation': {
        'name': 'slide',
        'exports': {
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
            'application/vnd.oasis.opendocument.presentation': 'odp',
            'application/pdf': 'pdf',
            'text/plain': 'txt'
        },
        'default_export': 'application/pdf'
    },
    'application/vnd.google-apps.script': {
        'name': 'script',
        'exports': {
            'application/vnd.google-apps.script+json': 'json'
        },
        'default_export': 'application/vnd.google-apps.script+json'
    },
}