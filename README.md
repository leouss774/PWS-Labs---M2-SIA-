# Shop — Web Services M2 SIA

Lab 1: the Inventory service, behind two doors.

## Run it

    docker compose up --build -d

Inventory: http://127.0.0.1:8000/docs — Orders: http://127.0.0.1:8001/docs

## Questions

1. In section 3, what status line did `DELETE /products/42` return, and what did
   the `allow` header say? Why that answer rather than a 404?
2. In section 4.5 the SOAP call failed. What did the HTTP status line say? Name one
   piece of infrastructure that is misled by it, and what it does wrong as a result.
3. Which of the two doors could a colleague use tomorrow without asking you anything?
   List precisely what they would need in each case.

## Lab 2 questions

1. In section 3.4 you sent the same PUT twice and, in section 4.3, the same order twice.
   What did each second request change? After a timeout, which one may a client resend
   without asking, and which one may it not?
2. Orders reserves stock with POST /products/{id}/reservations. Why not let Orders read
   the stock with GET, then write the new value with PATCH? Describe two orders arriving
   at the same moment for the last unit.
3. When Inventory is stopped, Orders answers 503. What would a client have received
   without the try/except, and why is that answer wrong?
4. In compose.yaml, Orders reaches Inventory at http://inventory:8000. Why not
   http://127.0.0.1:8000, which worked in section 4?

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

## Lab 2 answers

1. The second PUT changed nothing: the product already had the values sent, so the
   state of the server after two calls is the same as after one. PUT is idempotent,
   and a client may resend it after a timeout without asking. The second order
   changed things: it created a new order and reserved the units again, so the stock
   dropped twice (7 to 5 to 3). POST is not idempotent, and a client must not resend
   it blindly, because it cannot know whether the first attempt succeeded and would
   risk a duplicate order.

2. With GET then PATCH, two orders for the last unit arrive together. Both read
   `stock = 1`, both see enough stock, both write `stock = 0`, and both orders
   succeed: one unit is sold twice. The check and the write are two steps, and the
   second order slips in between them. `POST .../reservations` runs a single
   `UPDATE ... SET stock = stock - ? WHERE id = ? AND stock >= ?`: the database
   applies the first order, the condition fails for the second, and that one gets a
   `409 Conflict`.

3. Without the try/except, the `httpx.RequestError` would escape `place_order` and
   the client would receive `500 Internal Server Error`. That answer is wrong: a 500
   claims that Orders itself has a bug, while Orders works and its dependency is
   down. A client cannot tell what to do with a 500, whereas a 503 says the failure
   is temporary and the request can be retried later.

4. Inside a container, `127.0.0.1` is the container itself, and no Inventory runs in
   the Orders container. Compose puts both services on one network where each
   service name is a hostname, so `http://inventory:8000` reaches the Inventory
   container. On the laptop, both services ran on the same machine, so `127.0.0.1`
   worked.
