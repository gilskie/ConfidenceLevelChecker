import configparser
import sys
import os
import tempfile
import re
import ConfidenceLevelListClass
import csv


def main():
    config = configparser.ConfigParser()
    config_location = sys.path[0] + '\configuration.ini'
    config.read(config_location)

    default_setting = config["DEFAULT"]
    api_caller_folder_location = default_setting["api_caller_files"]
    dsd_no_correction_location = default_setting["dsd_no_correction_files"]
    report_output_location = default_setting["report_output"]

    api_files = os.listdir(api_caller_folder_location)
    dsd_files = os.listdir(dsd_no_correction_location)

    matched_files = []

    for file in api_files:
        file_name = file.replace('.xml','.out')
        if file_name in dsd_files:
            matched_files.append(file_name.replace('.out',''))

    gather_references_api_and_dsd(matched_files,
                                  api_caller_folder_location,
                                  dsd_no_correction_location,
                                  report_output_location)


# start gathering references that will be ready for search and replace of texts
def gather_references_api_and_dsd(matched_files,
                                  api_path,
                                  dsd_path,
                                  report_path):

    for file in matched_files:
        api_file_name = file + '.xml'
        dsd_file_name = file + '.out'

        # pattern below to be used for searching and replacing of texts.
        api_replace_texts = '(<brs:s l="[a-z]+">|&amp;amp;|</brs:s>|&amp;)'
        dsd_replace_texts = '(</?\w+([^>]+>|>)|&amp;amp;|&amp;)'
        # dsd_replace_texts = '(amp;|</?\w+([^>]+>|>)|&amp;amp;|&amp;)'

        api_input_file = open(os.path.join(api_path, api_file_name),
                              encoding="utf-8",
                              mode="rt")
        dsd_input_file = open(os.path.join(dsd_path, dsd_file_name),
                              encoding="utf-8",
                              mode="rt")

        api_output_temp = open(os.path.join(tempfile.gettempdir(),
                                            api_file_name),
                               encoding="utf-8",
                               mode="wt")
        dsd_output_temp = open(os.path.join(tempfile.gettempdir(),
                                            dsd_file_name),
                               encoding="utf-8",
                               mode="wt")

        # call function which will generate temp files then clean tags which will be ready for comparison purposes!
        generate_search_and_replace(api_input_file, api_replace_texts, api_output_temp)
        generate_search_and_replace(dsd_input_file, dsd_replace_texts, dsd_output_temp)

        api_input_file.close()
        dsd_input_file.close()
        api_output_temp.close()
        dsd_output_temp.close()

    gather_text_per_reference(matched_files, report_path)


# gather the text matching on the regular expression!
def gather_text_per_reference(matched_files, report_path):
    complete_list_matched_files = []

    for wms_job_name in matched_files:
        dsd_temp = open(os.path.join(tempfile.gettempdir(),wms_job_name + '.out'), encoding="utf-8", mode="rt")

        for line in dsd_temp:
            # match_text = re.findall(r'^\w+[^ ]+ \w+[^,]+,[^,]+,', line)
            match_text = re.findall(r'^\w+.*,', line)

            # print(f"match text: {match_text}|{wms_job_name}")
            # breakpoint()

            if len(match_text) > 0:
                complete_text = match_text[0]
                complete_text = str(complete_text).replace('(','\(').replace(')','\)')

                # print(f"complete text: {complete_text}")
                # breakpoint()

                complete_list_matched_files.append(ConfidenceLevelListClass.ConfidenceLevelList(wms_job_name,
                                                                                                complete_text, None))

    generate_match_per_confidence(complete_list_matched_files)
    generate_csv_report(report_path, complete_list_matched_files)


def generate_match_per_confidence(complete_list_matched_files):
    # check for a possible match for compiled list vs clean api caller output!
    for list_match in complete_list_matched_files:
        api_temp = open(os.path.join(tempfile.gettempdir(),
                                     list_match.jobname + '.xml'),
                        encoding="utf-8",
                        mode="rt")

        for line in api_temp:
            match_text = re.findall(r'(<brs:r [^>]+>)' + list_match.match_text, line)
            # print(f"(<brs:r [^>]+>){list_match.match_text}, match text:{match_text}")
            # breakpoint()

            if len(match_text) > 0:
                list_match.confidence_level = match_text[0]
                # print(f"Match: {match_text[0]}, actual text: {list_match.match_text}, job-name: {list_match.jobname}")


def generate_csv_report(report_path, complete_list_matched_files):
    # generate complete list of match vs no match using csv file!
    with open(os.path.join(report_path, 'ConfidenceLevelReport.csv'), mode='w', newline='') as confidence_report:
        confidence_writer = csv.writer(confidence_report, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        confidence_writer.writerow(['Job Name', 'Flagged Text', 'Gathered Confidence'])

        for list_jobs in complete_list_matched_files:
            confidence_writer.writerow([list_jobs.jobname,
                                        list_jobs.match_text,
                                        'None' if list_jobs.confidence_level is None else list_jobs.confidence_level])


# generate output temp files which will be used for comparison purposes and gathering of confidence level tag!
def generate_search_and_replace(input_file,
                                replace_text,
                                output_temp):
    for line in input_file:
        # start replacing texts to have match!
        temp_line = re.sub(replace_text, '', line)
        output_temp.write(temp_line if len(temp_line) > 0 else line)


main()