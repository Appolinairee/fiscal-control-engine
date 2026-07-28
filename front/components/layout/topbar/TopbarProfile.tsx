import Image from "next/image";

export default function TopbarProfile() {
  return (
    <div className="hidden items-center gap-5 sm:flex">
      <Image
        src="/assets/default-profile.jpeg"
        alt="Dwayne Tatum"
        width={58}
        height={58}
        priority
        className="size-[58px] shrink-0 rounded-full object-cover object-center"
      />

      <div className="w-[170px] min-w-0">
        <p className="truncate text-[16px] font-bold leading-[1.15] text-black">
          Dwayne Tatum
        </p>
        <p className="truncate text-[13px] font-semibold leading-[1.3] text-black">
          CEO Assistant
        </p>
      </div>
    </div>
  );
}
