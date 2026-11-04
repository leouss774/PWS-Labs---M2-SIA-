# Shop — Web Services M2 SIA

Lab 1: the Inventory service, behind two doors.

## Run it

    python -m uvicorn services.inventory.main:app --reload --port 3200

## Questions

1. In section 3, what status line did `DELETE /products/42` return, and what did
   the `allow` header say? Why that answer rather than a 404?
2. In section 4.5 the SOAP call failed. What did the HTTP status line say? Name one
   piece of infrastructure that is misled by it, and what it does wrong as a result.
3. Which of the two doors could a colleague use tomorrow without asking you anything?
   List precisely what they would need in each case.

## Answers

1. `DELETE /products/42` returned:

       HTTP/1.1 405 Method Not Allowed
       allow: GET

   The route `/products/{product_id}` exists, but it only declares `GET`.
   Therefore the server recognizes the path and rejects the unsupported method;
   this is a `405`, not a `404` (which would mean that no matching path
   existed).

2. The SOAP call returned:

       HTTP/1.1 200 OK

   even though the body contained a SOAP `env:Fault` saying `No product 99`.
   A monitoring or load-balancing component that only checks the HTTP status
   can therefore record the request as successful and avoid alerting or
   retrying it. A SOAP-aware client must inspect the envelope for the fault.

3. Both doors can be used without asking the author, provided the service is
   running. The REST door needs:

   - the base URL and port (with the documented command, `http://127.0.0.1:3200`);
   - `GET /products` for all products, or `GET /products/{id}` for one product;
   - an HTTP client such as `curl` (the `Accept` header is optional).

   The SOAP door needs:

   - the endpoint `POST /ProductService` on that same base URL;
   - `Content-Type: application/soap+xml`;
   - a SOAP 1.2 envelope using
     `http://www.w3.org/2003/05/soap-envelope`;
   - a `shop:GetProduct` body element in the
     `http://shop.example.com/` namespace, containing the requested
     `shop:id`.

   The provided [SOAP request](requests/get-product.xml) is a ready-made
   example. The low-level [HTTP script](tools/raw_http.py) also uses port
   `3200`.