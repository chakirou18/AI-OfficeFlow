"""Fixed private GHCR destinations and fail-closed visibility checks."""
import argparse
import json
import re
import subprocess


IMAGE_REPOSITORIES = {
    service: "ghcr.io/chakirou18/ai-officeflow-private-" + service
    for service in ("api", "frontend")
}


def output(command):
    result = subprocess.run(command, capture_output=True)
    if result.returncode:
        raise RuntimeError("Registry verification failed; raw output withheld")
    return result.stdout


def check_private_packages():
    # Packages must be provisioned and verified before hosted publication.
    # Repository permission inheritance does not guarantee private visibility.
    for repository in IMAGE_REPOSITORIES.values():
        name = repository.rsplit("/", 1)[1]
        package = json.loads(output(["gh", "api", "users/chakirou18/packages/container/" + name]))
        if (package.get("name") != name or package.get("visibility") != "private"
                or package.get("repository", {}).get("full_name") != "chakirou18/AI-OfficeFlow"):
            raise ValueError("Expected private repository-owned GHCR package")


def published_reference(service, commit):
    if service not in IMAGE_REPOSITORIES or not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("Invalid fixed image selection")
    repository = IMAGE_REPOSITORIES[service]
    references = json.loads(output(["docker", "image", "inspect", repository + ":" + commit,
                                    "--format", "{{json .RepoDigests}}"]))
    matches = [value for value in references or []
               if re.fullmatch(re.escape(repository) + r"@sha256:[a-f0-9]{64}", value)]
    if len(matches) != 1:
        raise ValueError("Expected exactly one digest for the private destination")
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["check", "reference"])
    parser.add_argument("service", nargs="?", choices=list(IMAGE_REPOSITORIES))
    parser.add_argument("commit", nargs="?")
    args = parser.parse_args()
    if args.action == "check":
        check_private_packages()
        print("Both fixed GHCR packages are private")
    else:
        print(published_reference(args.service, args.commit))


if __name__ == "__main__":
    main()
