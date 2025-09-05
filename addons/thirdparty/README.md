# Third-party addons

Place purchased/downloaded Odoo Apps modules here as **folders** (unzipped), for
example: addons/thirdparty/dental_hospital/...

Then build the image so the module is baked into /mnt/extra-addons:

## dev profile

ENV=dev sugar build

Module reference: Dental Hospital Management (technical name:
`dental_hospital`). Download requires sign-in on the Odoo Apps Store.
