# i-Xero2

This is a standardized and customized connector to Xero.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

This package supports the following version of Python. It probably supports older versions, but they have not been tested.

- Python 3.10 or later

### Installing

Install the latest package using pip.

```bash
$ pip install i-xero2
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Before running the tests, you need to authorize the app with Xero and save the tenant ID in the environment.

1. In Xero, switch to the "Demo Company".
1. Run the app locally.

    ```bash
    $ python app.py
    ```

1. In the browser, navigate to `http://localhost:5000/`
1. Follow the prompts to allow app to access Xero.
1. Read tenants.
1. Copy the `tenantId`.
1. Save the tenant id as an environment variable named `XERO_TENANT_ID`.
1. Run the tests.

    ```bash
    $ python -m pytest
    ```

## Usage

TODO

## Authors

- **Jason Romano** - [Aracnid](https://github.com/aracnid)

See also the list of [contributors](https://github.com/aracnid/i-xero2/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
