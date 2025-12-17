# httpx Library Example Queries

This document provides example queries specific to the httpx library with expected answer formats and citations.

## Example 1: SSL Certificate Validation

**Question:**
```
How does httpx validate SSL certificates?
```

**Actual Answer:**
```
HTTPX validates SSL certificates by default when making requests over HTTPS [docs/advanced/ssl.md:1-3]. It uses a bundle of SSL certificates, also known as a CA bundle, from a trusted certificate authority [docs/advanced/ssl.md:1-3]. By default, the `certifi` CA bundle is used for SSL verification [docs/advanced/ssl.md:23]. This default behavior sets the `SSLContext`'s `verify_mode` to `ssl.VerifyMode.CERT_REQUIRED` and `check_hostname` to `True` [tests/test_config.py:11-14].

Users can disable SSL verification completely by setting `verify=False` in requests, which allows insecure requests [docs/advanced/ssl.md:14-17]. When verification is disabled, the `SSLContext`'s `verify_mode` is set to `ssl.VerifyMode.CERT_NONE` and `check_hostname` to `False` [tests/test_config.py:76-79].

For more complex configurations, an `ssl.SSLContext` instance can be passed to the `Client()` or `httpx.get()` method [docs/advanced/ssl.md:20-21]. This context can be explicitly created and configured, for example, by specifying a `cafile` to `ssl.create_default_context()` [docs/advanced/ssl.md:24-28] or by using `context.load_verify_locations()` to load CA certificates from a file or directory [tests/test_config.py:82-86, tests/test_config.py:29-33, tests/test_config.py:36-40]. Client certificates can also be loaded into the `SSLContext` using `.load_cert_chain()` [docs/advanced/ssl.md:64-83, tests/test_config.py:43-47]. Additionally, `httpx` respects the `SSL_CERT_FILE` and `SSL_CERT_DIR` environment variables by default [docs/advanced/ssl.md:64-67].
```

**Evidence Quality**: Strong (multiple relevant chunks, high similarity)

## Example 2: Proxy Support Implementation

**Question:**
```
Where in the code is proxy support implemented?
```

**Actual Answer:**
```
Proxy support is implemented in several parts of the codebase. The `Client` and `AsyncClient` classes accept a `proxy` parameter during initialization to configure proxy usage [httpx/_client.py:623, httpx/_client.py:1335]. These classes use `_get_proxy_map` to process proxy configurations and `_init_proxy_transport` to set up transport layers for proxies [httpx/_client.py:649, httpx/_client.py:657-674, httpx/_client.py:688-699, httpx/_client.py:1361, httpx/_client.py:1369-1386, httpx/_client.py:1400-1411]. The `_transport_for_url` method then determines which transport, including a proxy transport, to use for a given URL [httpx/_client.py:701-709, httpx/_client.py:1413-1421].

The `Proxy` class in `httpx/_config.py` is responsible for parsing proxy URLs, handling authentication, and managing headers for proxy connections [httpx/_config.py:201-243].

The actual low-level proxy connection logic resides in the `HTTPTransport` and `AsyncHTTPTransport` classes within `httpx/_transports/default.py` [httpx/_transports/default.py:135-262, httpx/_transports/default.py:279-406]. These transports initialize an `httpcore.HTTPProxy` for HTTP/HTTPS proxies or an `httpcore.SOCKSProxy` for SOCKS5 proxies, based on the `proxy.url.scheme`, to route requests through the specified proxy [httpx/_transports/default.py:148-232, httpx/_transports/default.py:292-376]. Additionally, a `ProxyError` exception is defined for errors related to proxy connections [httpx/_exceptions.py:202-205].
```

**Evidence Quality**: Strong (multiple files, clear implementation locations)

## Example 3: Request Timeout Handling

**Question:**
```
What happens if a request exceeds the configured timeout?
```

**Actual Answer:**
```
If a request exceeds the configured timeout, a `TimeoutException` is raised [docs/advanced/timeouts.md:1-45, httpx/_exceptions.py:132-137]. More specific exceptions can also be raised depending on the type of timeout, such as `WriteTimeout` if a write operation times out [docs/advanced/timeouts.md:56-71, tests/test_timeouts.py:15-22], `ReadTimeout` if a read operation times out [tests/test_timeouts.py:6-12], or `PoolTimeout` if acquiring a connection from the pool exceeds the specified duration [docs/advanced/timeouts.md:56-71]. For instance, a test demonstrates that `httpx.TimeoutException` is raised for a send timeout [tests/test_timeouts.py:47-55].
```

**Evidence Quality**: Strong (clear timeout mechanism, exception handling)

## Example 4: Connection Pooling

**Question:**
```
How does httpx handle connection pooling?
```

**Actual Answer:**
```
HTTPX handles connection pooling by delegating to the `httpcore` library [httpx/_transports/default.py:135-144, httpx/_transports/default.py:279-288]. For synchronous operations, it uses `httpcore.ConnectionPool`, and for asynchronous operations, it uses `httpcore.AsyncConnectionPool` [httpx/_transports/default.py:146-159, httpx/_transports/default.py:290-303].

The connection pool can be configured with parameters such as `max_connections`, `max_keepalive_connections`, and `keepalive_expiry` [httpx/_transports/default.py:146-159, httpx/_transports/default.py:290-303]. These parameters are passed from the `limits` argument during the initialization of `HTTPTransport` or `AsyncHTTPTransport` [httpx/_transports/default.py:146-159, httpx/_transports/default.py:290-303].

There is a "pool timeout" which specifies the maximum duration to wait for acquiring a connection from the connection pool [docs/advanced/timeouts.md:56-58]. If a connection cannot be acquired within this timeframe, a `PoolTimeout` exception is raised [docs/advanced/timeouts.md:58-59, docs/exceptions.md:65-66]. The maximum number of allowable connections in the pool is configured by the `limits` argument [docs/advanced/timeouts.md:60-61]. Requests are handled by the internal `_pool` instance [httpx/_transports/default.py:249-250, httpx/_transports/default.py:389-390].
```

**Evidence Quality**: Strong (detailed implementation, multiple code locations)

## Example 5: HTTP/2 Support

**Question:**
```
Where is HTTP/2 support implemented?
```

**Actual Answer:**
```
HTTP/2 support in httpx is implemented by passing an `http2=True` parameter to the `Client` or `AsyncClient` constructors [httpx/_client.py:672, httpx/_client.py:1385]. When `http2` is enabled, the `h2` package is imported, and an `ImportError` is raised if it's not installed [httpx/_client.py:675-681, httpx/_client.py:1388-1394].

The `Client` and `AsyncClient` then initialize `HTTPTransport` or `AsyncHTTPTransport` respectively, passing the `http2` setting to them [httpx/_client.py:702-710, httpx/_client.py:713-724, httpx/_client.py:1415-1423, httpx/_client.py:1426-1437]. These transport classes, in turn, import `httpcore` and pass the `http2` parameter to `httpcore.ConnectionPool`, `httpcore.HTTPProxy`, or `httpcore.SOCKSProxy` instances [httpx/_transports/default.py:157, httpx/_transports/default.py:180, httpx/_transports/default.py:205, httpx/_transports/default.py:301, httpx/_transports/default.py:324, httpx/_transports/default.py:349]. This indicates that the low-level HTTP/2 protocol handling is delegated to the `httpcore` library.

Additionally, the command-line interface in `httpx/_main.py` includes an `--http2` option that allows users to send requests using HTTP/2, which is then passed to the `Client` constructor [httpx/_main.py:465-469, httpx/_main.py:490]. The `format_request_headers` function also uses an `http2` boolean to format headers and set the HTTP version string to "HTTP/2" when applicable [httpx/_main.py:116-126]. The `http_version` property in `httpx/_models.py` can retrieve "HTTP/2" from response extensions [httpx/_models.py:610-617].
```

**Evidence Quality**: Strong (comprehensive HTTP/2 implementation details)

## Example 6: Retry Handling

**Question:**
```
How does httpx handle retries?
```

**Actual Answer:**
```
HTTPX handles retries by allowing a `retries` parameter to be specified in its `HTTPTransport` and `AsyncHTTPTransport` classes [httpx/_transports/default.py:135, httpx/_transports/default.py:279]. This `retries` parameter, which defaults to `0`, is then passed to the `httpcore.ConnectionPool` or `httpcore.AsyncConnectionPool` instances that manage the connections [httpx/_transports/default.py:157, httpx/_transports/default.py:301].
```

**Evidence Quality**: Strong (clear implementation, though concise answer)

## Example 7: No Evidence Response

**Question:**
```
What is the Krabby Patty recipe?
```

**Actual Answer:**
```
I couldn't find relevant code in the repository to answer this question.

The repository may not contain code related to your question, or the code might be indexed under different terms. Try rephrasing your question or checking if the repository has been fully indexed.
```

**Evidence Quality**: No evidence (question is unrelated to the codebase)

**Note**: This demonstrates ASKII's guardrail behavior when asked about topics completely unrelated to the codebase. The system correctly refuses to speculate and provides a helpful message.

## Citation Format Notes

All citations follow the format `[file_path:line_range]`:
- `[httpx/_client.py:120-145]` - Lines 120 to 145 in httpx/_client.py
- `[httpx/_transports/base.py:150-180]` - Lines 150 to 180 in httpx/_transports/base.py
- Multiple citations: `[file1.py:10-20, file2.py:5-15]` - Multiple sources supporting a claim

## Usage

To run these queries against a local httpx repository:

```bash
# Clone httpx repository
git clone https://github.com/encode/httpx.git
cd httpx

# Run a query
askii "How does httpx validate SSL certificates?"

# Or specify the path explicitly
askii "Where in the code is proxy support implemented?" --repository-path /path/to/httpx
```

## Notes

- These examples show expected formats; actual answers may vary based on the specific codebase version
- File paths and line numbers are illustrative and may differ in actual httpx codebase
- Evidence quality indicators help understand when ASKII has found strong vs. weak evidence
- Weak evidence scenarios demonstrate how ASKII handles uncertainty

