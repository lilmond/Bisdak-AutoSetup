def get_num_domain(num: int):
    x = 0

    while True:
        if num <= x + 50:
            domain_num = f"{x + 1}-{x + 50}"
            break

        x += 50

    domain = f"bisdaknode{domain_num}.ovh"

    return domain

num = 101
x = get_num_domain(num)
print(x)
