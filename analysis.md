# analysis

## question 1 - highest inefficiency ratio

Sao Paulo has the highest inefficiency ratio at 6.86. Its theoretical minimum is only 22.3 ms because it is the closest city at 2230 km, but the measured RTT was 153 ms. Looking at submarinecablemap.com, Sao Paulo is served by the Seabras-1 cable, which runs directly to New Jersey, and the EllaLink cable, which connects to Europe. Despite this direct cable to the US east coast, all Google URLs from Boston resolve to nearby US servers due to CDNs, adding a fixed overhead that is proportionally very large for a close city like Sao Paulo, driving the ratio up significantly.

## question 2 - closest to theoretical minimum

Singapore has the lowest inefficiency ratio at 1.14, meaning its measured RTT of 150.6 ms is only 14 percent above the theoretical minimum of 131.8 ms. Singapore is the farthest city at 13176 km, so its theoretical minimum is already high. Singapore is one of the most connected internet hubs in Asia with dozens of submarine cables and major internet exchange points, meaning routing overhead is minimal. Because the theoretical minimum is already large due to distance, the fixed overhead adds proportionally little, pushing the ratio close to 1.0. This shows that well connected cities with low routing overhead can come close to the physical speed of light limit.

## question 3 - why Lagos routes through Europe

Lagos and most of West Africa route traffic through Europe because the submarine cable infrastructure was historically built by European telecommunications companies. Cables like WACS and ACE run northward along the African coast and terminate in the UK, Portugal, and France. There are no major direct cables connecting West Africa to North America, so a packet from Boston to Lagos must first cross the Atlantic to Europe and then travel back south along the African coast, adding significant extra distance and delay. Research from Carnegie Mellon University found that much of the content used in Africa is hosted in Europe, and that traffic between African countries is often routed through Europe as well. To fix this, direct submarine cables connecting West Africa to North America would need to be built, along with local internet exchange points within Africa so that regional traffic does not need to leave the continent.
