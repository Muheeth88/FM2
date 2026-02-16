import json
import xml.etree.ElementTree as ET
import os


class BuildMetadataExtractor:

    @staticmethod
    def extract(repo_root, build_system):
        deps = []
        pom_path = os.path.join(repo_root, "pom.xml")

        if build_system == "maven" and os.path.exists(pom_path):
            try:
                # Handle namespaces
                tree = ET.parse(pom_path)
                root = tree.getroot()
                
                # Maven usually has a namespace. Let's find it.
                ns = ""
                if root.tag.startswith("{"):
                    ns = root.tag.split("}")[0] + "}"
                
                # xpath with namespace
                for dep in root.findall(f".//{ns}dependency"):
                    group = dep.find(f"{ns}groupId")
                    artifact = dep.find(f"{ns}artifactId")
                    version = dep.find(f"{ns}version")

                    if artifact is not None:
                        deps.append({
                            "name": artifact.text,
                            "version": version.text if version is not None else "managed",
                            "type": "runtime"
                        })
            except Exception as e:
                print(f"Error parsing pom.xml: {str(e)}")

        elif build_system == "npm":
            pkg_path = os.path.join(repo_root, "package.json")
            if os.path.exists(pkg_path):
                try:
                    with open(pkg_path, "r") as f:
                        package_json = json.load(f)
                    for name, version in package_json.get("dependencies", {}).items():
                        deps.append({"name": name, "version": version, "type": "runtime"})
                    for name, version in package_json.get("devDependencies", {}).items():
                        deps.append({"name": name, "version": version, "type": "dev"})
                except Exception:
                    pass

        return deps
