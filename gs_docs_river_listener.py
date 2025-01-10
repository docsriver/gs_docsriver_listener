#!/usr/bin/python3

import http.server
import json
import os.path
import subprocess
import json
import re

PORT_NUMBER = 9080
DOCS_RIVER_FILES_PATH = '/opt/docsriver/virtual_pdfs_output'
server = None

def clean_output(stdout):
    """
    переписано из js
        stdout = stdout
            .split('\n')
            .filter(l => !l.startsWith('   **** ') && l.length > 0)
            .join('\n')
            .trim();
    """
    lines = stdout.splitlines()
    filtered_lines = [line for line in lines if not re.match(r'^   \*\*\*\* ', line)]
    return '\n'.join(filtered_lines).strip()

class GsCommandsHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.get('content-length'))
        post_body = self.rfile.read(content_len)
        print("POST request (headers, body):",
              str(self.headers), post_body.decode('utf-8'))

        data = json.loads(post_body)

        if data["command"] == "ping":
            (status, output, err) = self._run_ping_command(data["testfile"])
            self._write_command_response(output, err)
            return
        if data["command"] == "ps2pdf":
            (status, output, err) = self._run_ps_to_pdf_command(data["psfile"], data["pdffile"])
            self._write_command_response(output, err)
            return
        if data["command"] == "countPages":
            (status, output, err) = self._run_count_pages_command(data["pdffile"])
            self._write_command_response(output, err)
            return

        if data["command"] == "extractPDFPages":
            (status, output, err) = self._run_extract_pdf_pages(data["pdffile"], data['start'], data['end'], data['output'])
            self._write_command_response(output, err)
            return
        if data["command"] == "extractPDFImagesPages":
            (status, output, err) = self._run_extract_pdf_image_pages(data["pdffile"], data['start'], data['end'], data['output'], data['is_monochrom'])
            self._write_command_response(output, err)
            return

        self._set_headers()

        return

    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def _set_error_headers(self):
        self.send_response(400)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    @staticmethod
    def _normalize_file_name(file_name: str):
        if file_name.startswith('/'):
            return file_name[1:]
        else:
            return file_name

    def _run_ping_command(self, testfile: str):
        testfile_path = os.path.join(DOCS_RIVER_FILES_PATH, self._normalize_file_name(testfile))
        with open(testfile_path, 'r') as file:
            text = file.read()
        print("Ping")
        return 200, text, None


    def _run_ps_to_pdf_command(self, ps_file: str, pdf_file: str):
        ps_path = os.path.join(DOCS_RIVER_FILES_PATH, self._normalize_file_name(ps_file))
        pdf_path = os.path.join(DOCS_RIVER_FILES_PATH, self._normalize_file_name(pdf_file))
        print("PS File:", ps_path)
        print("PDF File:", pdf_path)
        p = subprocess.Popen(["ps2pdf", ps_path, pdf_path], stdout=subprocess.PIPE)
        p_status = p.wait()
        (p_output, p_error) = p.communicate()
        return p_status, p_output, p_error

    def _run_count_pages_command(self, pdf_file: str):
        pdf_path = os.path.join(DOCS_RIVER_FILES_PATH, self._normalize_file_name(pdf_file))
        print("PDF File:", pdf_path)
        count_command = 'gs -q -dNOPAUSE -dBATCH -dNOSAFER -dNODISPLAY -c "({}) (r) file runpdfbegin pdfpagecount = quit"'.format(pdf_path)
        ls_command = ["ls", "-l", pdf_path]
        p = subprocess.Popen(count_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p_status = p.wait()
        (p_output, p_error) = p.communicate()
        return p_status, clean_output(p_output.decode()), p_error

    def _run_extract_pdf_pages(self, pdf_file: str, start: int, end: int, output: str):
        pdf_path = os.path.join(DOCS_RIVER_FILES_PATH, self._normalize_file_name(pdf_file))
        out_path = os.path.join(DOCS_RIVER_FILES_PATH, self._normalize_file_name(output))
        print("PDF File:", pdf_path)
        print("Result PDF File:", out_path)
        # gs -q -dNOPAUSE -sDEVICE=pdfwrite -dBATCH -dNOSAFER -dFirstPage=${firstPage} -dLastPage=${lastPage} -dAutoRotatePages=/None -sOutputFile=${output} ${input}
        command = 'gs -q -dNOPAUSE -sDEVICE=pdfwrite -dBATCH -dNOSAFER -dFirstPage={} -dLastPage={} -dAutoRotatePages=/None -sOutputFile={} {}'.format(start, end, out_path, pdf_path)
        p = subprocess.Popen(command, shell=True)
        p_status = p.wait()
        (p_output, p_error) = p.communicate()
        return p_status, p_output, p_error

    def _run_extract_pdf_image_pages(self, pdf_file: str, start: int, end: int, output: str, is_monochrom: bool):
        pdf_path = os.path.join(DOCS_RIVER_FILES_PATH, self._normalize_file_name(pdf_file))
        out_path = os.path.join(DOCS_RIVER_FILES_PATH, self._normalize_file_name(output))
        print("PDF File:", pdf_path)
        print("Result PDF File:", out_path)
        device = "pdfimage8" if is_monochrom else "pdfimage32"
        print("Device:", device)
        # gs -q -dNOPAUSE -sDEVICE=pdfwrite -dBATCH -dNOSAFER -dFirstPage=${firstPage} -dLastPage=${lastPage} -dAutoRotatePages=/None -sOutputFile=${output} ${input}
        command = 'gs -q -dNOPAUSE -sDEVICE={} -r300 -dBATCH -dNOSAFER -dFirstPage={} -dLastPage={} -dAutoRotatePages=/None -sOutputFile={} {}'.format(device, start, end, out_path, pdf_path)
        p = subprocess.Popen(command, shell=True)
        p_status = p.wait()
        (p_output, p_error) = p.communicate()
        return p_status, p_output, p_error


    def _write_command_response(self, output, err):
        if err is not None:
            content = json.dumps({'status': 'ERROR', 'message': str(err)})
            self._set_error_headers()
            self.wfile.write(content.encode())
        elif output is not None:
            content = json.dumps({'status': 'OK', 'message': str(output)})
            self._set_headers()
            self.wfile.write(content.encode())
        else:
            content = json.dumps({'status': 'OK'})
            self._set_headers()
            self.wfile.write(content.encode())


try:
    server = http.server.HTTPServer(('', PORT_NUMBER), GsCommandsHandler)
    print('Started GS HTTP server on port ', PORT_NUMBER)
    server.serve_forever()

except KeyboardInterrupt:
    print('^C received, shutting down the web server')
    server.socket.close()
