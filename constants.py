from pydrive.auth import GoogleAuth
import yaml

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

SDR_RELPATH = '.sdr'
TEMP_DIR_RELPATH = SDR_RELPATH + '/temp'
DRIVE_FILES_RELPATH = SDR_RELPATH + '/gdrive.json'
SDR_CONFIG_RELPATH = SDR_RELPATH + '/config.json'
GAUTH_CREDENTIALS_RELPATH = SDR_RELPATH + '/gauth_credentials.json'
GAUTH_SETTINGS_RELPATH = SDR_RELPATH + '/gauth_settings.yaml'
GAUTH_SETTINGS: str = yaml.dump({**GoogleAuth.DEFAULT_SETTINGS, **{'client_config_file': GAUTH_CREDENTIALS_RELPATH}})

GDRIVE_QUERY = '\'{}\' in parents and trashed=false'
DIRECTORY_EXPECTED_ERROR_MSG = 'Error: Directory `{}` does not exist.'
INVALID_BACKREFERENCE_ERROR_MSG = 'Error: Targeted directory is outside of the file system.'

CHOSEN_GDRIVE_DIR_PATH_KEY = 'chosen_gdrive_dir'
