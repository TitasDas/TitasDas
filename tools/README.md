# Profile teasers

`teaser.py` builds the looping GIFs in `assets/`. They are 656x492 so they stay sharp at the 328 px GitHub shows them at: a solid headline band on top with one short idea per beat, a clean crop of the product underneath, and a closing card that points to the walkthrough. Source frames come from each product's walkthrough pipeline (see the `tools/walkthrough` folders in the product repos). Run `python3 teaser.py wd|fm|dd|rs|ps` from the folder that holds those frames.
