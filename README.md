
[![Commit Activity](https://img.shields.io/github/commit-activity/m/Luftfartsverket/reqstool-python-hatch-plugin?label=commits&style=for-the-badge)](https://github.com/Luftfartsverket/reqstool-python-hatch-plugin/pulse)
[![GitHub Issues](https://img.shields.io/github/issues/Luftfartsverket/reqstool-python-hatch-plugin?style=for-the-badge&logo=github)](https://github.com/Luftfartsverket/reqstool-python-hatch-plugin/issues)
[![License](https://img.shields.io/github/license/Luftfartsverket/reqstool-python-hatch-plugin?style=for-the-badge&logo=opensourceinitiative)](https://opensource.org/license/mit/)
[![Build](https://img.shields.io/github/actions/workflow/status/Luftfartsverket/reqstool-python-hatch-plugin/build.yml?style=for-the-badge&logo=github)](https://github.com/Luftfartsverket/reqstool-python-hatch-plugin/actions/workflows/build.yml)
[![Static Badge](https://img.shields.io/badge/Documentation-blue?style=for-the-badge&link=docs)](https://luftfartsverket.github.io/reqstool-python-hatch-plugin/reqstool-python-hatch-plugin/0.0.2/index.html)



## Description

This documentation provides information on how to use the Reqstool Hatch Plugin. The plugin is designed to be used with the Hatch build tool and facilitates the integration of the Reqstool Decorators in your project.

## Installation

To use the Reqstool Hatch Plugin, follow these steps:

- Update your project dependencies in the `pyproject.toml` file and 
ensure that the Reqstool Decorators' dependency is listed as follows;
``` 
dependencies = ["reqstool-python-decorators == <version>"]
```

When you declare this in the pyproject.toml file, you are specifying the required versions for the dependency of the Reqstool Decorators. This ensures that the correct version of the dependencies are used when installing and running your project.



## Usage



### Configuration

The plugin can be configured through the `pyproject.toml` file. Configure plugin in `pyproject.toml`as follows;

```
[tool.hatch.build.targets.wheel.hooks.decorators]
dependencies = ["reqstool-hatch-plugin == <version>"]
path = ["src","tests"]

```
It specifies that the reqstool-hatch-plugin is a dependency for the build process, and it should be of a specific version. 

Further it defines the paths where the plugin should be applied. In this case, it specifies that the plugin should be applied to files in the src and tests directories. 
