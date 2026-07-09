"""Health probing for tool containers."""

import concurrent.futures
import logging
from typing import Set

from deps import get_client, get_codeql_client, get_linguist_client

logger = logging.getLogger(__name__)


def probe_all_tools() -> Set[str]:
    """Probe all tools and return a set of healthy tool names."""
    import config.tools as tools_module

    healthy = set()

    def check_spec(spec):
        try:
            client = get_client(spec.name)
            # If the health check succeeds, it returns the JSON payload (or raises on failure)
            client.get_health()
            return spec.name
        except Exception as e:
            logger.debug(f"Tool {spec.name} is not healthy: {e}")
        return None

    # max_workers=17 handles the ~52 total probes efficiently (~4 waves if all timeout).
    # This prevents the 10s worst-case timeout from stacking serially into 520s.
    with concurrent.futures.ThreadPoolExecutor(max_workers=17) as executor:
        futures = []
        for spec in tools_module._SPECS:
            futures.append(executor.submit(check_spec, spec))

        def check_standalone(name):
            try:
                if name == "codeql":
                    get_codeql_client().get_health()
                elif name == "linguist":
                    get_linguist_client().get_health()
                return name
            except Exception as e:
                logger.debug(f"Standalone tool {name} is not healthy: {e}")
                return None

        futures.append(executor.submit(check_standalone, "codeql"))
        futures.append(executor.submit(check_standalone, "linguist"))

        for future in concurrent.futures.as_completed(futures):
            name = future.result()
            if name:
                healthy.add(name)

    return healthy


def update_healthy_tools() -> Set[str]:
    """Probe all tools and remove unhealthy ones from the registry."""
    import config.tools as tools_module

    logger.info("Probing container health...")
    healthy = probe_all_tools()
    logger.info(f"Healthy tools: {healthy}")

    tools_module.filter_unhealthy_tools(healthy)

    return healthy
