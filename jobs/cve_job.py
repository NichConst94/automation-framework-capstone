from nautobot.core.celery import register_jobs
from nautobot.apps.jobs import Job
from nautobot_device_lifecycle_mgmt.models import CVELCM, SoftwareLCM

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import requests
import os
import json


class ProvisionCVE(Job):
    class Meta:
        name = "Provision CVEs"
        description = "Pull CVEs from the internet and propogate them into Nautobot."

    cves = []
    cves_id = []

    def scrape_webpage(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(
            "https://sec.cloudapps.cisco.com/security/center/publicationListing.x"
        )
        driver.implicitly_wait(5)
        time.sleep(7)
        page_source = driver.page_source
        driver.quit()

        soup = BeautifulSoup(page_source, "html.parser")
        data = soup.find_all("span", class_="ng-binding")

        cve_add_count = 0
        for i in range(0, len(data)):
            if data[i].text.startswith("CVE") and data[i].text not in self.cves:
                self.cves.append(data[i].text)
                cve_add_count += 1
            elif (
                data[i].text.startswith("cisco-sa") and data[i].text not in self.cves_id
            ):
                if cve_add_count == 2:
                    self.cves_id.append(data[i].text)
                    self.cves_id.append(data[i].text)
                    cve_add_count = 0
                else:
                    self.cves_id.append(data[i].text)
                    cve_add_count = 0

    def download_file(self, url, filename):
        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Open a new file in binary write mode and write the content of the response
            with open(filename, "wb") as f:
                f.write(response.content)

    def extract_service_packs(self, data, target_product_family):
        service_packs = []

        if isinstance(data, dict):
            # Check if the current node represents a branch
            if (
                "name" in data
                and data.get("category") == "product_family"
                and data.get("name") == target_product_family
            ):
                # Extract service packs directly under the target product family
                if "branches" in data:
                    for branch in data["branches"]:
                        if (
                            branch.get("category") == "product_version"
                            and "branches" in branch
                        ):
                            for sub_branch in branch["branches"]:
                                if (
                                    sub_branch.get("category") == "service_pack"
                                    and "name" in sub_branch
                                ):
                                    # Append the service pack name to the list
                                    service_packs.append(sub_branch["name"])
            else:
                # Recursively search deeper if the current node has nested branches
                if "branches" in data:
                    for branch in data["branches"]:
                        service_packs.extend(
                            self.extract_service_packs(branch, target_product_family)
                        )

        return service_packs

    def run(self):
        self.scrape_webpage()

        nautobot_softwares = []
        nautobot_cves = []
        for cve in CVELCM.objects.all():
            nautobot_cves.append(cve.name)
        for software in SoftwareLCM.objects.all():
            nautobot_softwares.append(
                f"{software.device_platform} - {software.version}"
            )

        # If CVE is not already in nautobot
        for cve in self.cves:
            if cve not in nautobot_cves:
                cve_download_url = (
                    "https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/"
                    + self.cves_id[self.cves.index(cve)]
                    + "/csaf/"
                    + self.cves_id[self.cves.index(cve)]
                    + ".json"
                )
                cve_file_name = "cve_file.json"
                self.download_file(cve_download_url, cve_file_name)

                # Load JSON data from the file
                with open(cve_file_name, "r", encoding="utf-8") as file:
                    json_data = json.load(file)

                # Extract service packs under the specified product family
                ios_service_packs = self.extract_service_packs(
                    json_data["product_tree"], "IOS"
                )
                ios_xe_service_packs = self.extract_service_packs(
                    json_data["product_tree"], "Cisco IOS XE Software"
                )
                ios_softwares = []
                ios_xe_softwares = []
                if ios_service_packs:
                    for pack in ios_service_packs:
                        ios_softwares.append(f"Cisco IOS - {pack}")
                if ios_xe_service_packs:
                    for pack in ios_xe_service_packs:
                        ios_xe_softwares.append(f"Cisco IOS-XE - {pack}")

                if ios_softwares or ios_xe_softwares:
                    cve_object = None
                    cve_date = json_data["document"]["tracking"]["initial_release_date"]
                    cve_date = cve_date[:10]
                    cve_link = (
                        "https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/"
                        + self.cves_id[self.cves.index(cve)]
                    )
                    cve_score = json_data["vulnerabilities"][0]["scores"][0]["cvss_v3"][
                        "baseScore"
                    ]
                    cve_severity = json_data["vulnerabilities"][0]["scores"][0][
                        "cvss_v3"
                    ]["baseSeverity"]
                    cve_severity = cve_severity.lower()
                    cve_severity = cve_severity[0].upper() + cve_severity[1:]
                    for software in ios_softwares:
                        if software in nautobot_softwares:
                            cve_object = CVELCM(
                                name=cve,
                                published_date=cve_date,
                                link=cve_link,
                                cvss=cve_score,
                                severity=cve_severity,
                            )
                            cve_object.validated_save()
                            break
                    if cve_object == None:
                        for software in ios_xe_softwares:
                            if software in nautobot_softwares:
                                cve_object = CVELCM(
                                    name=cve,
                                    published_date=cve_date,
                                    link=cve_link,
                                    cvss=cve_score,
                                    severity=cve_severity,
                                )
                                cve_object.validated_save()
                                break

                    if cve_object != None:
                        for software in ios_softwares:
                            if software in nautobot_softwares:
                                device_platform_name, version_number = software.split(
                                    " - "
                                )
                                cve_object.affected_softwares.add(
                                    SoftwareLCM.objects.get(
                                        device_platform__name=device_platform_name,
                                        version=version_number,
                                    )
                                )
                        for software in ios_xe_softwares:
                            if software in nautobot_softwares:
                                device_platform_name, version_number = software.split(
                                    " - "
                                )
                                cve_object.affected_softwares.add(
                                    SoftwareLCM.objects.get(
                                        device_platform__name=device_platform_name,
                                        version=version_number,
                                    )
                                )
                        cve_object.validated_save()

                os.remove(cve_file_name)


register_jobs(ProvisionCVE)
