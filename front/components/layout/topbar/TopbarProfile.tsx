import Image from "next/image";

export default function TopbarProfile() {
  return (
    <div className="hidden items-center gap-5 sm:flex">
      <Image
        src="/assets/default-profile.jpeg"
        alt="Dwayne Tatum"
        width={54}
        height={54}
        priority
        className="size-[54px] shrink-0 rounded-full object-cover object-center"
      />

      <div className="flex h-[54px] w-[170px] min-w-0 flex-col justify-center">
        <p className="truncate text-[16px] font-bold leading-[1.08] text-black">
          Dwayne Tatum
        </p>
        <p className="truncate text-[13px] font-semibold leading-[1.25] text-black">
          CEO Assistant
        </p>
      </div>
    </div>
  );
}
