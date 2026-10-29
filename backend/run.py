"""Single-process container entry point, honoring the platform-assigned PORT."""
import os
import logging
import uvicorn


def main():
    port = int(os.getenv('PORT', '8000'))
    if not 1 <= port <= 65535:
        raise ValueError('PORT must be between 1 and 65535')
    logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper(),
                        format='%(levelname)s %(name)s %(message)s')
    uvicorn.run('backend.main:app', host='0.0.0.0', port=port,
                log_level=os.getenv('LOG_LEVEL', 'info'), timeout_graceful_shutdown=20,
                forwarded_allow_ips=os.getenv('FORWARDED_ALLOW_IPS', '127.0.0.1'))


if __name__ == '__main__':
    main()
