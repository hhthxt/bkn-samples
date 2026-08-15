from pathlib import Path


PACK = Path(__file__).resolve().parents[2]


def test_function_service_deployment_artifacts_exist():
    assert (PACK / "Dockerfile.function").is_file()
    assert (PACK / "docker-compose.function.yaml").is_file()


def test_function_deployment_does_not_embed_host_docker_internal():
    compose = (PACK / "docker-compose.function.yaml").read_text(encoding="utf-8")
    dockerfile = (PACK / "Dockerfile.function").read_text(encoding="utf-8")
    assert "host.docker.internal" not in compose
    assert "host.docker.internal" not in dockerfile
